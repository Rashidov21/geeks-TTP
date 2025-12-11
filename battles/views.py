from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db.models import Q
from .models import Battle, BattleParticipant
from typing_practice.models import Text, CodeSnippet
from typing_practice.utils import get_random_text, get_random_code
import json
import logging

logger = logging.getLogger('typing_platform')


@login_required
def battle_list(request):
    """List all battles"""
    # Get pending battles (waiting for opponent)
    pending_battles = Battle.objects.filter(
        status='pending',
        opponent__isnull=True
    ).exclude(creator=request.user).select_related('creator').order_by('-created_at')[:20]
    
    # Get user's battles
    user_battles = Battle.objects.filter(
        Q(creator=request.user) | Q(opponent=request.user)
    ).select_related('creator', 'opponent', 'winner').order_by('-created_at')[:20]
    
    return render(request, 'battles/list.html', {
        'pending_battles': pending_battles,
        'user_battles': user_battles,
    })


@login_required
def battle_create(request):
    """Create a new battle"""
    if request.method == 'POST':
        mode = request.POST.get('mode', 'text')
        
        # Get random text or code
        if mode == 'text':
            text = get_random_text()
            if not text:
                messages.error(request, 'Matnlar mavjud emas.')
                return redirect('battles:list')
            battle = Battle.objects.create(
                creator=request.user,
                mode=mode,
                text=text
            )
        else:
            # Get random code (any language, easy difficulty)
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
                code_snippet=code
            )
        
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
    
    return render(request, 'battles/play.html', {
        'battle': battle,
    })


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
        except (ValueError, TypeError, json.JSONDecodeError) as e:
            return JsonResponse({'error': 'Noto\'g\'ri ma\'lumot formati'}, status=400)
        
        # Save or update participant result
        participant, created = BattleParticipant.objects.get_or_create(
            battle=battle,
            user=request.user
        )
        
        participant.wpm = wpm
        participant.accuracy = accuracy
        participant.mistakes = mistakes
        participant.is_finished = True
        participant.finished_at = timezone.now()
        participant.save()
        
        # Check if both participants finished
        finished_count = battle.participants.filter(is_finished=True).count()
        battle_finished = False
        if finished_count == 2:
            # Determine winner
            participants = battle.participants.all().order_by('-wpm', '-accuracy')
            if participants.count() == 2:
                winner = participants.first().user
                battle.winner = winner
                battle.finish()
                battle_finished = True
        
        return JsonResponse({
            'success': True,
            'wpm': wpm,
            'accuracy': accuracy,
            'mistakes': mistakes,
            'battle_finished': battle_finished,
        })
        
    except Exception as e:
        logger.error(f"Error saving battle result: {e}", exc_info=True)
        return JsonResponse({'error': 'Server xatosi yuz berdi'}, status=500)
