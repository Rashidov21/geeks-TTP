from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db.models import Q
from django.core.cache import cache
from .models import Battle, BattleParticipant, BattleRating, BattleInvitation
from typing_practice.models import Text, CodeSnippet
from typing_practice.utils import get_random_text, get_random_code
from .utils import (
    update_battle_ratings, award_battle_rewards, determine_battle_winner,
    find_match_for_user, get_active_users
)
from accounts.models import Notification
import json
import logging
from datetime import timedelta

logger = logging.getLogger('typing_platform')


@login_required
def battle_list(request):
    """List all battles with filters"""
    # Get filter parameters
    status_filter = request.GET.get('status', '')
    mode_filter = request.GET.get('mode', '')
    search_query = request.GET.get('search', '')
    
    # Get pending battles (waiting for opponent)
    pending_battles = Battle.objects.filter(
        status='pending',
        opponent__isnull=True
    ).exclude(creator=request.user).select_related('creator')
    
    if mode_filter:
        pending_battles = pending_battles.filter(mode=mode_filter)
    
    pending_battles = pending_battles.order_by('-created_at')[:20]
    
    # Get user's battles
    user_battles = Battle.objects.filter(
        Q(creator=request.user) | Q(opponent=request.user)
    ).select_related('creator', 'opponent', 'winner')
    
    if status_filter:
        user_battles = user_battles.filter(status=status_filter)
    if mode_filter:
        user_battles = user_battles.filter(mode=mode_filter)
    if search_query:
        user_battles = user_battles.filter(
            Q(creator__username__icontains=search_query) |
            Q(opponent__username__icontains=search_query)
        )
    
    user_battles = user_battles.order_by('-created_at')[:20]
    
    # Get user's battle rating
    try:
        user_rating = BattleRating.objects.get(user=request.user)
    except BattleRating.DoesNotExist:
        user_rating = None
    
    return render(request, 'battles/list.html', {
        'pending_battles': pending_battles,
        'user_battles': user_battles,
        'user_rating': user_rating,
        'status_filter': status_filter,
        'mode_filter': mode_filter,
        'search_query': search_query,
    })


@login_required
def battle_create(request):
    """Create a new battle"""
    if request.method == 'POST':
        mode = request.POST.get('mode', 'text')
        battle_type = request.POST.get('battle_type', 'balanced')
        time_limit = int(request.POST.get('time_limit', 300))
        countdown = int(request.POST.get('countdown', 3))
        rematch_id = request.POST.get('rematch_id', None)
        
        # Get random text or code
        if mode == 'text':
            text = get_random_text()
            if not text:
                messages.error(request, 'Matnlar mavjud emas.')
                return redirect('battles:list')
            battle = Battle.objects.create(
                creator=request.user,
                mode=mode,
                text=text,
                battle_type=battle_type,
                time_limit_seconds=time_limit,
                countdown_seconds=countdown,
            )
        else:
            # Get random code
            from typing_practice.models import CodeSnippet
            import random
            code_ids = list(CodeSnippet.objects.values_list('id', flat=True))
            if not code_ids:
                messages.error(request, 'Kod namunasi mavjud emas.')
                return redirect('battles:list')
            random_id = random.choice(code_ids)
            code = CodeSnippet.objects.get(id=random_id)
            
            battle = Battle.objects.create(
                creator=request.user,
                mode=mode,
                code_snippet=code,
                battle_type=battle_type,
                time_limit_seconds=time_limit,
                countdown_seconds=countdown,
            )
        
        # Handle rematch
        if rematch_id:
            try:
                original_battle = Battle.objects.get(id=rematch_id)
                battle.rematch_of = original_battle
                battle.save()
            except Battle.DoesNotExist:
                pass
        
        # Create participant for creator
        BattleParticipant.objects.create(battle=battle, user=request.user)
        
        messages.success(request, 'Jang yaratildi! Raqibni kutish...')
        return redirect('battles:detail', battle_id=battle.id)
    
    return redirect('battles:list')


@login_required
def battle_join(request, battle_id):
    """Join a battle as opponent"""
    battle = get_object_or_404(Battle, id=battle_id)
    
    if battle.creator == request.user:
        messages.error(request, 'Siz bu jangni yaratgansiz.')
        return redirect('battles:detail', battle_id=battle.id)
    
    if battle.opponent:
        messages.error(request, 'Bu jangga allaqachon qo\'shilgan.')
        return redirect('battles:detail', battle_id=battle.id)
    
    if battle.status != 'pending':
        messages.error(request, 'Bu jangga qo\'shilish mumkin emas.')
        return redirect('battles:detail', battle_id=battle.id)
    
    battle.opponent = request.user
    battle.save()
    
    # Create participant for opponent
    BattleParticipant.objects.create(battle=battle, user=request.user)
    
    # Start the battle
    battle.start()
    
    messages.success(request, 'Jangga qo\'shildingiz!')
    return redirect('battles:play', battle_id=battle.id)


@login_required
def battle_detail(request, battle_id):
    """View battle details"""
    battle = get_object_or_404(
        Battle.objects.select_related('creator', 'opponent', 'winner', 'text', 'code_snippet'),
        id=battle_id
    )
    
    # Check if user is participant
    is_participant = battle.creator == request.user or battle.opponent == request.user
    
    if not is_participant:
        messages.error(request, 'Siz bu jangda ishtirok etmaysiz.')
        return redirect('battles:list')
    
    participants = battle.participants.all().select_related('user')
    creator_result = participants.filter(user=battle.creator).first()
    opponent_result = participants.filter(user=battle.opponent).first() if battle.opponent else None
    
    return render(request, 'battles/detail.html', {
        'battle': battle,
        'creator_result': creator_result,
        'opponent_result': opponent_result,
        'can_join': battle.status == 'pending' and not battle.opponent and battle.creator != request.user,
        'can_play': battle.status == 'active' and is_participant,
    })


@login_required
def battle_play(request, battle_id):
    """Play the battle"""
    battle = get_object_or_404(
        Battle.objects.select_related('creator', 'opponent', 'text', 'code_snippet'),
        id=battle_id
    )
    
    # Check if user is participant
    if battle.creator != request.user and battle.opponent != request.user:
        messages.error(request, 'Siz bu jangda ishtirok etmaysiz.')
        return redirect('battles:list')
    
    if battle.status != 'active':
        messages.error(request, 'Jang faol emas.')
        return redirect('battles:detail', battle_id=battle.id)

    # Prevent playing if participant already finished
    participant = BattleParticipant.objects.filter(battle=battle, user=request.user).first()
    if participant and participant.is_finished:
        messages.error(request, 'Siz bu jangni tugatgansiz.')
        return redirect('battles:detail', battle_id=battle.id)
    
    return render(request, 'battles/play.html', {
        'battle': battle,
    })


@login_required
@require_http_methods(["POST"])
def battle_update_progress(request, battle_id):
    """Update real-time progress during battle (without finishing)"""
    try:
        battle = get_object_or_404(Battle, id=battle_id)
        
        if battle.status != 'active':
            return JsonResponse({'error': 'Jang faol emas'}, status=400)
        
        # Check if user is participant
        if battle.creator != request.user and battle.opponent != request.user:
            return JsonResponse({'error': 'Siz bu jangda ishtirok etmaysiz'}, status=403)
        
        # Parse data
        try:
            data = json.loads(request.body)
            from typing_practice.utils import validate_wpm, validate_accuracy
            wpm = validate_wpm(data.get('wpm', 0))
            accuracy = validate_accuracy(data.get('accuracy', 0))
            mistakes = max(0, int(data.get('mistakes', 0)))
            progress = float(data.get('progress', 0))  # 0-100
        except (ValueError, TypeError, json.JSONDecodeError) as e:
            logger.warning(f"Invalid data in battle_update_progress: {e}")
            return JsonResponse({'error': 'Noto\'g\'ri ma\'lumot formati'}, status=400)
        
        # Save or update participant result (without marking as finished)
        participant, created = BattleParticipant.objects.get_or_create(
            battle=battle,
            user=request.user
        )
        
        # Update real-time progress (don't set is_finished=True)
        participant.wpm = wpm
        participant.accuracy = accuracy
        participant.mistakes = mistakes
        participant.progress_percent = min(100, max(0, progress))
        # Don't set is_finished or finished_at here
        participant.save()
        
        return JsonResponse({
            'success': True,
            'wpm': wpm,
            'progress': progress,
        })
    except Exception as e:
        logger.error(f"Error updating battle progress: {e}", exc_info=True)
        return JsonResponse({'error': 'Xatolik yuz berdi'}, status=500)


@login_required
@require_http_methods(["POST"])
def battle_save_result(request, battle_id):
    """Save battle result"""
    try:
        battle = get_object_or_404(Battle, id=battle_id)
        
        if battle.status != 'active':
            return JsonResponse({'error': 'Jang faol emas'}, status=400)
        
        # Check if user is participant
        if battle.creator != request.user and battle.opponent != request.user:
            return JsonResponse({'error': 'Siz bu jangda ishtirok etmaysiz'}, status=403)
        
        # Parse data
        try:
            data = json.loads(request.body)
            from typing_practice.utils import validate_wpm, validate_accuracy
            wpm = validate_wpm(data.get('wpm', 0))
            accuracy = validate_accuracy(data.get('accuracy', 0))
            mistakes = max(0, int(data.get('mistakes', 0)))
            progress = float(data.get('progress', 0))  # 0-100
        except (ValueError, TypeError, json.JSONDecodeError) as e:
            logger.warning(f"Invalid data in battle_save_result: {e}")
            return JsonResponse({'error': 'Noto\'g\'ri ma\'lumot formati'}, status=400)
        
        # Save or update participant result
        participant, created = BattleParticipant.objects.get_or_create(
            battle=battle,
            user=request.user
        )
        
        participant.wpm = wpm
        participant.accuracy = accuracy
        participant.mistakes = mistakes
        participant.progress_percent = min(100, max(0, progress))
        participant.is_finished = True
        participant.finished_at = timezone.now()
        participant.save()
        
        # Check if both participants finished
        finished_count = battle.participants.filter(is_finished=True).count()
        battle_finished = False
        if finished_count == 2:
            # Determine winner based on battle type
            winner = determine_battle_winner(battle)
            battle.winner = winner
            battle.finish()
            battle_finished = True
            
            # Update ratings and award rewards
            update_battle_ratings(battle)
            award_battle_rewards(battle)
            
            # Send notifications
            if winner:
                Notification.objects.create(
                    user=winner,
                    notification_type='achievement',
                    title='Battle g\'alabasi!',
                    message=f'🎉 {battle.opponent.username if winner == battle.creator else battle.creator.username} ustidan g\'alaba qozondingiz!',
                    icon='🎉',
                    link=f'/battles/{battle.id}/'
                )
                Notification.objects.create(
                    user=battle.opponent if winner == battle.creator else battle.creator,
                    notification_type='battle',
                    title='Battle natijasi',
                    message=f'Jang tugadi. {winner.username} g\'olib bo\'ldi.',
                    icon='⚔️',
                    link=f'/battles/{battle.id}/'
                )
        
        logger.info(f"Battle result saved: user={request.user.username}, battle={battle_id}, wpm={wpm}")
        
        return JsonResponse({
            'success': True,
            'wpm': wpm,
            'accuracy': accuracy,
            'mistakes': mistakes,
            'battle_finished': battle_finished,
            'winner': battle.winner.username if battle.winner else None,
        })
        
    except Battle.DoesNotExist:
        logger.warning(f"Battle not found: battle_id={battle_id}")
        return JsonResponse({'error': 'Jang topilmadi'}, status=404)
    except Exception as e:
        logger.error(f"Error saving battle result: {e}", exc_info=True)
        return JsonResponse({'error': 'Server xatosi yuz berdi'}, status=500)


@login_required
def battle_rematch(request, battle_id):
    """Create a rematch of a finished battle"""
    original_battle = get_object_or_404(Battle, id=battle_id)
    
    if original_battle.status != 'finished':
        messages.error(request, 'Faqat tugallangan janglarni rematch qilish mumkin.')
        return redirect('battles:detail', battle_id=battle_id)
    
    # Check if user was participant
    if original_battle.creator != request.user and original_battle.opponent != request.user:
        messages.error(request, 'Siz bu jangda ishtirok etmadingiz.')
        return redirect('battles:list')
    
    # Create new battle with same settings
    if original_battle.mode == 'text':
        battle = Battle.objects.create(
            creator=request.user,
            opponent=original_battle.opponent if original_battle.opponent != request.user else original_battle.creator,
            mode=original_battle.mode,
            text=original_battle.text,
            battle_type=original_battle.battle_type,
            time_limit_seconds=original_battle.time_limit_seconds,
            countdown_seconds=original_battle.countdown_seconds,
            rematch_of=original_battle,
        )
    else:
        battle = Battle.objects.create(
            creator=request.user,
            opponent=original_battle.opponent if original_battle.opponent != request.user else original_battle.creator,
            mode=original_battle.mode,
            code_snippet=original_battle.code_snippet,
            battle_type=original_battle.battle_type,
            time_limit_seconds=original_battle.time_limit_seconds,
            countdown_seconds=original_battle.countdown_seconds,
            rematch_of=original_battle,
        )
    
    # Create participants
    BattleParticipant.objects.create(battle=battle, user=battle.creator)
    BattleParticipant.objects.create(battle=battle, user=battle.opponent)
    
    # Start battle immediately
    battle.start()
    
    messages.success(request, 'Rematch yaratildi!')
    return redirect('battles:play', battle_id=battle.id)


@login_required
def battle_quick_match(request):
    """Auto-matchmaking: find opponent and create battle"""
    if request.method == 'POST':
        mode = request.POST.get('mode', 'text')
        battle_type = request.POST.get('battle_type', 'balanced')
        time_limit = int(request.POST.get('time_limit', 300))
        
        # Find opponent
        opponent = find_match_for_user(request.user, mode, battle_type, time_limit)
        
        if not opponent:
            messages.error(request, 'Hozircha mos raqib topilmadi. Keyinroq urinib ko\'ring.')
            return redirect('battles:list')
        
        # Create battle
        if mode == 'text':
            text = get_random_text()
            if not text:
                messages.error(request, 'Matnlar mavjud emas.')
                return redirect('battles:list')
            battle = Battle.objects.create(
                creator=request.user,
                opponent=opponent,
                mode=mode,
                text=text,
                battle_type=battle_type,
                time_limit_seconds=time_limit,
                is_auto_match=True,
            )
        else:
            from typing_practice.models import CodeSnippet
            import random
            code_ids = list(CodeSnippet.objects.values_list('id', flat=True))
            if not code_ids:
                messages.error(request, 'Kod namunasi mavjud emas.')
                return redirect('battles:list')
            random_id = random.choice(code_ids)
            code = CodeSnippet.objects.get(id=random_id)
            
            battle = Battle.objects.create(
                creator=request.user,
                opponent=opponent,
                mode=mode,
                code_snippet=code,
                battle_type=battle_type,
                time_limit_seconds=time_limit,
                is_auto_match=True,
            )
        
        # Create participants
        BattleParticipant.objects.create(battle=battle, user=request.user)
        BattleParticipant.objects.create(battle=battle, user=opponent)
        
        # Start battle
        battle.start()
        
        # Send notification to opponent
        Notification.objects.create(
            user=opponent,
            notification_type='battle',
            title='Yangi battle taklifi!',
            message=f'{request.user.username} sizni battlega taklif qildi!',
            icon='⚔️',
            link=f'/battles/{battle.id}/play/'
        )
        
        messages.success(request, f'Raqib topildi: {opponent.username}!')
        return redirect('battles:play', battle_id=battle.id)
    
    return redirect('battles:list')


@login_required
def battle_invite(request):
    """Send battle invitation to a user"""
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        mode = request.POST.get('mode', 'text')
        battle_type = request.POST.get('battle_type', 'balanced')
        time_limit = int(request.POST.get('time_limit', 300))
        
        if not username:
            messages.error(request, 'Foydalanuvchi nomi kiritilmadi.')
            return redirect('battles:list')
        
        try:
            to_user = User.objects.get(username=username)
        except User.DoesNotExist:
            messages.error(request, f'"{username}" foydalanuvchi topilmadi.')
            return redirect('battles:list')
        
        if to_user == request.user:
            messages.error(request, 'O\'zingizga taklif yuborib bo\'lmaydi.')
            return redirect('battles:list')
        
        # Create invitation
        expires_at = timezone.now() + timedelta(minutes=5)
        invitation = BattleInvitation.objects.create(
            from_user=request.user,
            to_user=to_user,
            battle_mode=mode,
            battle_type=battle_type,
            time_limit_seconds=time_limit,
            expires_at=expires_at,
        )
        
        # Send notification
        Notification.objects.create(
            user=to_user,
            notification_type='battle',
            title='Battle taklifi',
            message=f'{request.user.username} sizni battlega taklif qildi!',
            icon='⚔️',
            link=f'/battles/invitations/{invitation.id}/'
        )
        
        messages.success(request, f'{to_user.username} ga taklif yuborildi!')
        return redirect('battles:list')
    
    return redirect('battles:list')


@login_required
def battle_invitation_respond(request, invitation_id):
    """Respond to battle invitation"""
    invitation = get_object_or_404(BattleInvitation, id=invitation_id, to_user=request.user)
    
    if invitation.status != 'pending':
        messages.error(request, 'Bu taklifga allaqachon javob berilgan.')
        return redirect('battles:list')
    
    if invitation.is_expired():
        invitation.status = 'expired'
        invitation.save()
        messages.error(request, 'Taklifning muddati tugagan.')
        return redirect('battles:list')
    
    action = request.GET.get('action', '')
    
    if action == 'accept':
        # Create battle
        if invitation.battle_mode == 'text':
            text = get_random_text()
            if not text:
                messages.error(request, 'Matnlar mavjud emas.')
                return redirect('battles:list')
            battle = Battle.objects.create(
                creator=invitation.from_user,
                opponent=request.user,
                mode=invitation.battle_mode,
                text=text,
                battle_type=invitation.battle_type,
                time_limit_seconds=invitation.time_limit_seconds,
            )
        else:
            from typing_practice.models import CodeSnippet
            import random
            code_ids = list(CodeSnippet.objects.values_list('id', flat=True))
            if not code_ids:
                messages.error(request, 'Kod namunasi mavjud emas.')
                return redirect('battles:list')
            random_id = random.choice(code_ids)
            code = CodeSnippet.objects.get(id=random_id)
            
            battle = Battle.objects.create(
                creator=invitation.from_user,
                opponent=request.user,
                mode=invitation.battle_mode,
                code_snippet=code,
                battle_type=invitation.battle_type,
                time_limit_seconds=invitation.time_limit_seconds,
            )
        
        # Create participants
        BattleParticipant.objects.create(battle=battle, user=battle.creator)
        BattleParticipant.objects.create(battle=battle, user=battle.opponent)
        
        # Start battle
        battle.start()
        
        # Update invitation
        invitation.status = 'accepted'
        invitation.battle = battle
        invitation.responded_at = timezone.now()
        invitation.save()
        
        messages.success(request, 'Taklif qabul qilindi!')
        return redirect('battles:play', battle_id=battle.id)
    
    elif action == 'reject':
        invitation.status = 'rejected'
        invitation.responded_at = timezone.now()
        invitation.save()
        
        messages.info(request, 'Taklif rad etildi.')
        return redirect('battles:list')
    
    return redirect('battles:list')


@login_required
@require_http_methods(["GET"])
def battle_opponent_progress(request, battle_id):
    """Get opponent's real-time progress (API endpoint)"""
    battle = get_object_or_404(Battle, id=battle_id)
    
    if battle.creator != request.user and battle.opponent != request.user:
        return JsonResponse({'error': 'Ruxsat berilmagan'}, status=403)
    
    opponent = battle.opponent if battle.creator == request.user else battle.creator
    participant = BattleParticipant.objects.filter(battle=battle, user=opponent).first()
    
    if participant:
        # Return current WPM even if not finished (for real-time chart)
        return JsonResponse({
            'wpm': participant.wpm,  # Show real-time WPM, not just when finished
            'accuracy': participant.accuracy if participant.is_finished else None,
            'progress': participant.progress_percent,
            'is_finished': participant.is_finished,
        })
    else:
        return JsonResponse({
            'wpm': None,
            'accuracy': None,
            'progress': 0,
            'is_finished': False,
        })
