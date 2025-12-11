from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.cache import cache
from django.db.models import Avg
from django.db import transaction
from .models import Competition, CompetitionParticipant, CompetitionStage, CompetitionParticipantStage, Certificate
from typing_practice.models import Text, CodeSnippet
from typing_practice.utils import get_random_text, get_random_code
import json
import secrets
import random
import logging

logger = logging.getLogger('typing_platform')


@login_required
def competition_list(request):
    # Show all public competitions and user's competitions with optimized queries
    cache_key_all = 'competitions_all_public'
    cache_key_user = f'competitions_user_{request.user.id}'
    
    all_competitions = cache.get(cache_key_all)
    if all_competitions is None:
        all_competitions = Competition.objects.filter(
            is_public=True
        ).select_related('created_by').prefetch_related('participants').order_by('-start_time')[:20]
        cache.set(cache_key_all, list(all_competitions), 120)  # 2 minutes
    
    user_competitions = cache.get(cache_key_user)
    if user_competitions is None:
        user_competitions = Competition.objects.filter(
            participants=request.user
        ).select_related('created_by').prefetch_related('participants').order_by('-start_time')[:20]
        cache.set(cache_key_user, list(user_competitions), 120)  # 2 minutes
    
    return render(request, 'competitions/list.html', {
        'user_competitions': user_competitions,
        'all_competitions': all_competitions,
    })


@login_required
def competition_detail(request, competition_id):
    competition = get_object_or_404(
        Competition.objects.select_related('created_by'),
        id=competition_id
    )
    
    # Check if user can view (public or participant)
    if not competition.is_public:
        is_participant = CompetitionParticipant.objects.filter(
            user=request.user,
            competition=competition
        ).exists()
        if not is_participant and not request.user.userprofile.is_manager:
            messages.error(request, 'Bu musobaqa shaxsiy.')
            return redirect('competitions:list')
    
    participant = CompetitionParticipant.objects.filter(
        user=request.user,
        competition=competition
    ).select_related('user').first()
    
    # Get all participants with results - optimized
    participants = CompetitionParticipant.objects.filter(
        competition=competition
    ).select_related('user').order_by('-result_wpm')
    
    # Get stages with related objects
    stages = CompetitionStage.objects.filter(
        competition=competition
    ).select_related('text', 'code_snippet').order_by('stage_number')
    
    is_owner = competition.created_by == request.user
    can_join = request.user.userprofile.is_manager or participant is not None or competition.is_public
    
    return render(request, 'competitions/detail.html', {
        'competition': competition,
        'participant': participant,
        'participants': participants,
        'stages': stages,
        'is_owner': is_owner,
        'can_join': can_join,
    })


@login_required
def competition_create(request):
    if not request.user.userprofile.is_manager:
        messages.error(request, 'Only managers can create competitions')
        return redirect('competitions:list')
    
    if request.method == 'POST':
        name = request.POST.get('name')
        mode = request.POST.get('mode')
        difficulty = request.POST.get('difficulty', 'easy')
        start_time = request.POST.get('start_time')
        user_ids = request.POST.getlist('participants')
        access_code = request.POST.get('access_code', '').strip()
        is_public = request.POST.get('is_public') == 'on'
        enable_certificates = request.POST.get('enable_certificates') == 'on'
        organization_name = request.POST.get('organization_name', '').strip()
        certificate_subtitle = request.POST.get('certificate_subtitle', '').strip()
        signature_name = request.POST.get('signature_name', '').strip()
        additional_names = request.POST.get('additional_names', '').strip()
        logo = request.FILES.get('logo')
        
        if not access_code:
            access_code = secrets.token_urlsafe(8)
        
        competition = Competition.objects.create(
            name=name,
            mode=mode,
            difficulty=difficulty,
            start_time=start_time,
            created_by=request.user,
            access_code=access_code,
            is_public=is_public,
            enable_certificates=enable_certificates,
            status='pending'
        )
        
        # Create certificate if enabled
        if enable_certificates:
            cert, _ = Certificate.objects.get_or_create(competition=competition)
            # Update certificate fields from form
            if organization_name:
                cert.organization_name = organization_name
            if certificate_subtitle:
                cert.certificate_subtitle = certificate_subtitle
            if signature_name:
                cert.signature_name = signature_name
            if additional_names:
                cert.additional_names = additional_names
            if logo:
                cert.logo = logo
            cert.save()
        
        # Create 3 stages with random texts/codes (optimized)
        with transaction.atomic():
            if mode == 'text':
                # Get all available texts for this difficulty
                from typing_practice.models import Text
                available_texts = list(Text.objects.filter(difficulty=difficulty).values_list('id', flat=True))
                
                if len(available_texts) < 3:
                    messages.error(request, f'Yetarli matnlar topilmadi (kamida 3 ta kerak, hozir {len(available_texts)} ta mavjud).')
                    competition.delete()
                    return redirect('competitions:list')
                
                # Select 3 random unique texts
                import random
                selected_text_ids = random.sample(available_texts, min(3, len(available_texts)))
                selected_texts = Text.objects.filter(id__in=selected_text_ids)
                
                for i, text in enumerate(selected_texts, 1):
                    CompetitionStage.objects.create(
                        competition=competition,
                        stage_number=i,
                        text=text
                    )
                    
            elif mode == 'code':
                # Use optimized random selection
                selected_codes = []
                for _ in range(3):
                    code = get_random_code('python', difficulty)  # Default to python, can be extended
                    if code and code not in selected_codes:
                        selected_codes.append(code)
                    if len(selected_codes) >= 3:
                        break
                
                if len(selected_codes) >= 3:
                    for i, code in enumerate(selected_codes, 1):
                        CompetitionStage.objects.create(
                            competition=competition,
                            stage_number=i,
                            code_snippet=code
                        )
                else:
                    messages.error(request, 'Yetarli kodlar topilmadi (kamida 3 ta kerak).')
                    competition.delete()
                    return redirect('competitions:list')
        
        # Add participants
        if user_ids:
            from django.contrib.auth.models import User
            users = User.objects.filter(id__in=user_ids)
            competition.participants.set(users)
        
        messages.success(request, f'Competition "{name}" created with 3 stages!')
        return redirect('competitions:detail', competition_id=competition.id)
    
    # GET request
    from django.contrib.auth.models import User
    users = User.objects.filter(userprofile__is_manager=False)
    
    return render(request, 'competitions/create.html', {
        'users': users,
    })


@login_required
def competition_join(request, competition_id):
    competition = get_object_or_404(Competition, id=competition_id)
    
    if request.method == 'POST':
        access_code = request.POST.get('access_code', '')
        
        if competition.access_code and access_code != competition.access_code:
            messages.error(request, 'Invalid access code')
            return redirect('competitions:detail', competition_id=competition.id)
        
        participant, created = CompetitionParticipant.objects.get_or_create(
            user=request.user,
            competition=competition
        )
        
        if created:
            messages.success(request, 'You have joined the competition!')
        else:
            messages.info(request, 'You are already in this competition')
        
        return redirect('competitions:detail', competition_id=competition.id)
    
    return redirect('competitions:detail', competition_id=competition.id)


@login_required
def competition_start(request, competition_id):
    competition = get_object_or_404(Competition, id=competition_id)
    
    if competition.created_by != request.user:
        messages.error(request, 'Only the creator can start the competition')
        return redirect('competitions:detail', competition_id=competition.id)
    
    competition.status = 'active'
    competition.save()
    
    messages.success(request, 'Competition started!')
    return redirect('competitions:detail', competition_id=competition.id)


@login_required
def competition_finish(request, competition_id):
    competition = get_object_or_404(Competition, id=competition_id)
    
    if competition.created_by != request.user:
        messages.error(request, 'Only the creator can finish the competition')
        return redirect('competitions:detail', competition_id=competition.id)
    
    competition.status = 'finished'
    competition.save()
    
    # Create certificate if enabled and not already created
    if competition.enable_certificates:
        Certificate.objects.get_or_create(competition=competition)
    
    messages.success(request, 'Competition finished!')
    return redirect('competitions:results', competition_id=competition.id)


@login_required
def competition_play(request, competition_id, stage_number=1):
    competition = get_object_or_404(
        Competition.objects.select_related('created_by'),
        id=competition_id
    )
    
    participant = CompetitionParticipant.objects.filter(
        user=request.user,
        competition=competition
    ).select_related('user').first()
    
    if not participant:
        messages.error(request, 'Siz bu musobaqada qatnashmadingiz')
        return redirect('competitions:detail', competition_id=competition.id)
    
    if competition.status != 'active':
        messages.error(request, 'Musobaqa faol emas')
        return redirect('competitions:detail', competition_id=competition.id)
    
    # Validate stage number
    if stage_number < 1 or stage_number > 3:
        messages.error(request, 'Noto\'g\'ri bosqich raqami')
        return redirect('competitions:detail', competition_id=competition.id)
    
    # Check if stages exist, if not create them
    stages_count = CompetitionStage.objects.filter(competition=competition).count()
    if stages_count == 0:
        # Create stages for old competitions
        from typing_practice.models import Text, CodeSnippet
        import random
        
        if competition.mode == 'text':
            available_texts = list(Text.objects.filter(difficulty=competition.difficulty).values_list('id', flat=True))
            if len(available_texts) >= 3:
                selected_text_ids = random.sample(available_texts, min(3, len(available_texts)))
                selected_texts = Text.objects.filter(id__in=selected_text_ids)
                for i, text in enumerate(selected_texts, 1):
                    CompetitionStage.objects.get_or_create(
                        competition=competition,
                        stage_number=i,
                        defaults={'text': text}
                    )
            else:
                messages.error(request, 'Musobaqa uchun matnlar topilmadi. Iltimos, admin bilan bog\'laning.')
                return redirect('competitions:detail', competition_id=competition.id)
        elif competition.mode == 'code':
            available_codes = list(CodeSnippet.objects.filter(
                language='python',
                difficulty=competition.difficulty
            ).values_list('id', flat=True))
            if len(available_codes) >= 3:
                selected_code_ids = random.sample(available_codes, min(3, len(available_codes)))
                selected_codes = CodeSnippet.objects.filter(id__in=selected_code_ids)
                for i, code in enumerate(selected_codes, 1):
                    CompetitionStage.objects.get_or_create(
                        competition=competition,
                        stage_number=i,
                        defaults={'code_snippet': code}
                    )
            else:
                messages.error(request, 'Musobaqa uchun kodlar topilmadi. Iltimos, admin bilan bog\'laning.')
                return redirect('competitions:detail', competition_id=competition.id)
    
    # Get current stage with related objects
    stage = get_object_or_404(
        CompetitionStage.objects.select_related('text', 'code_snippet'),
        competition=competition,
        stage_number=stage_number
    )
    
    # Get or create participant stage
    participant_stage, created = CompetitionParticipantStage.objects.get_or_create(
        participant=participant,
        stage=stage
    )
    
    # Check attempts limit
    if not participant_stage.can_attempt():
        messages.error(request, f'Siz bu bosqich uchun maksimal urinishlar soniga ({competition.max_attempts_per_stage}) yetdingiz')
        return redirect('competitions:detail', competition_id=competition.id)
    
    if created and stage_number == 1:
        participant.started_at = timezone.now()
        participant.current_stage = 1
        participant.save()
    
    if not participant_stage.started_at:
        participant_stage.started_at = timezone.now()
        participant_stage.save()
    
    # Get all stages for navigation
    all_stages = CompetitionStage.objects.filter(
        competition=competition
    ).select_related('text', 'code_snippet').order_by('stage_number')
    
    return render(request, 'competitions/play.html', {
        'competition': competition,
        'participant': participant,
        'stage': stage,
        'participant_stage': participant_stage,
        'stage_number': stage_number,
        'all_stages': all_stages,
    })


@login_required
@require_http_methods(["POST"])
def competition_save_result(request, competition_id, stage_number):
    """Save competition stage result with validation"""
    try:
        competition = get_object_or_404(Competition, id=competition_id)
        
        # Validate competition is active
        if competition.status != 'active':
            return JsonResponse({'error': 'Musobaqa faol emas'}, status=400)
        
        participant = CompetitionParticipant.objects.select_related('user').get(
            user=request.user,
            competition=competition
        )
        
        # Validate stage number
        if stage_number < 1 or stage_number > 3:
            return JsonResponse({'error': 'Noto\'g\'ri bosqich raqami'}, status=400)
        
        stage = get_object_or_404(CompetitionStage, competition=competition, stage_number=stage_number)
        
        # Parse and validate data
        try:
            data = json.loads(request.body)
            from typing_practice.utils import validate_wpm, validate_accuracy
            wpm = validate_wpm(data.get('wpm', 0))
            accuracy = validate_accuracy(data.get('accuracy', 0))
            mistakes = max(0, int(data.get('mistakes', 0)))
        except (ValueError, TypeError, json.JSONDecodeError) as e:
            logger.warning(f"Invalid data in competition_save_result: {e}")
            return JsonResponse({'error': 'Noto\'g\'ri ma\'lumot formati'}, status=400)
        
        # Save stage result with transaction
        with transaction.atomic():
            participant_stage, created = CompetitionParticipantStage.objects.get_or_create(
                participant=participant,
                stage=stage
            )
            
            # Check attempts limit
            if not participant_stage.can_attempt():
                return JsonResponse({'error': f'Siz bu bosqich uchun maksimal urinishlar soniga ({competition.max_attempts_per_stage}) yetdingiz'}, status=400)
            
            # Increment attempts
            participant_stage.attempts += 1
            
            # Only update results if this attempt is better or first attempt
            if not participant_stage.is_finished or (wpm > (participant_stage.wpm or 0)):
                participant_stage.wpm = wpm
                participant_stage.accuracy = accuracy
                participant_stage.mistakes = mistakes
                participant_stage.is_finished = True
                participant_stage.finished_at = timezone.now()
            
            participant_stage.save()
            
            # Update participant current stage
            if stage_number < 3:
                participant.current_stage = stage_number + 1
            else:
                participant.current_stage = 4  # All stages completed
                participant.is_finished = True
                participant.finished_at = timezone.now()
            
            # Calculate average results using model method
            participant.calculate_average_results()
        
        # Clear competition cache
        cache.delete(f'competition_{competition_id}_participants')
        cache.delete('competitions_all_public')
        cache.delete(f'competitions_user_{request.user.id}')
        
        logger.info(f"Competition result saved: user={request.user.username}, competition={competition_id}, stage={stage_number}, wpm={wpm}")
        
        return JsonResponse({
            'success': True,
            'next_stage': stage_number + 1 if stage_number < 3 else None,
            'finished': stage_number >= 3
        })
    
    except CompetitionParticipant.DoesNotExist:
        logger.warning(f"Participant not found: user={request.user.username}, competition={competition_id}")
        return JsonResponse({'error': 'Siz bu musobaqada qatnashmadingiz'}, status=403)
    except Exception as e:
        logger.error(f"Error saving competition result: {e}", exc_info=True)
        return JsonResponse({'error': 'Server xatosi yuz berdi'}, status=500)


@login_required
def competition_results(request, competition_id):
    competition = get_object_or_404(
        Competition.objects.select_related('created_by'),
        id=competition_id
    )
    
    # Check if user can view (public or participant)
    if not competition.is_public:
        is_participant = CompetitionParticipant.objects.filter(
            user=request.user,
            competition=competition
        ).exists()
        if not is_participant and not request.user.userprofile.is_manager:
            messages.error(request, 'Bu musobaqa shaxsiy.')
            return redirect('competitions:list')
    
    # Get all participants with optimized query
    participants = CompetitionParticipant.objects.filter(
        competition=competition
    ).select_related('user').prefetch_related(
        'stage_results__stage'
    ).order_by('-result_wpm')

    # Top 3 participants (for certificates preview)
    top_three = list(participants[:3])
    
    # Ensure all participants have calculated results (including mistakes)
    for participant in participants:
        if not participant.mistakes or participant.mistakes == 0:
            participant.calculate_average_results()
    
    # Re-fetch participants to get updated mistakes
    participants = CompetitionParticipant.objects.filter(
        competition=competition
    ).select_related('user').prefetch_related(
        'stage_results__stage'
    ).order_by('-result_wpm')
    
    # Get stages
    stages = CompetitionStage.objects.filter(
        competition=competition
    ).select_related('text', 'code_snippet').order_by('stage_number')
    
    # Get stage results for each participant (already prefetched)
    participant_results = {}
    for participant in participants:
        participant_results[participant.id] = {
            'participant': participant,
            'stages': {}
        }
        for stage_result in participant.stage_results.all():
            participant_results[participant.id]['stages'][stage_result.stage.stage_number] = stage_result
    
    # Find user's rank for certificate link
    user_rank = None
    user_participant = None
    for idx, participant in enumerate(participants, 1):
        if participant.user == request.user:
            user_rank = idx
            user_participant = participant
            break
    
    return render(request, 'competitions/results.html', {
        'competition': competition,
        'participants': participants,
        'stages': stages,
        'participant_results': participant_results,
        'user_rank': user_rank,
        'user_participant': user_participant,
        'top_three': top_three,
    })


@login_required
def competition_certificate(request, competition_id, rank=None):
    """Display certificate for top 3 winners or user's own certificate"""
    competition = get_object_or_404(
        Competition.objects.select_related('created_by'),
        id=competition_id
    )
    
    # Only show certificates for finished competitions
    if competition.status != 'finished':
        messages.error(request, 'Musobaqa hali tugallanmagan')
        return redirect('competitions:detail', competition_id=competition.id)
    
    # Get participant at this rank
    participants = CompetitionParticipant.objects.filter(
        competition=competition,
        is_finished=True
    ).select_related('user').order_by('-result_wpm')
    
    # If rank is not provided, show user's own certificate if they are in top 3
    if rank is None:
        # Find user's rank
        user_participant = participants.filter(user=request.user).first()
        if not user_participant:
            messages.error(request, 'Siz bu musobaqada ishtirok etmadingiz')
            return redirect('competitions:results', competition_id=competition.id)
        
        # Find user's rank
        user_rank = None
        for idx, participant in enumerate(participants, 1):
            if participant.user == request.user:
                user_rank = idx
                break
        
        if user_rank and user_rank <= 3:
            rank = user_rank
            winner = user_participant
        else:
            messages.error(request, 'Siz top 3 talikda emassiz, sertifikat faqat 1, 2, 3 o\'rinlar uchun')
            return redirect('competitions:results', competition_id=competition.id)
    else:
        # Only allow ranks 1, 2, 3
        if rank not in [1, 2, 3]:
            messages.error(request, 'Noto\'g\'ri o\'rin raqami')
            return redirect('competitions:results', competition_id=competition.id)
        
        if participants.count() < rank:
            messages.error(request, 'Bu o\'rin uchun sertifikat mavjud emas')
            return redirect('competitions:results', competition_id=competition.id)
        
        winner = participants[rank - 1]
        
        # Check if user is the winner or admin
        if winner.user != request.user and not (hasattr(request.user, 'userprofile') and request.user.userprofile.is_manager):
            messages.error(request, 'Siz bu sertifikatni ko\'ra olmaysiz')
            return redirect('competitions:results', competition_id=competition.id)
    
    # Get or create certificate (should already exist if enable_certificates is True)
    certificate, created = Certificate.objects.get_or_create(competition=competition)
    
    # Get all winners for display
    top_three = list(participants[:3])
    
    return render(request, 'competitions/certificate.html', {
        'competition': competition,
        'winner': winner,
        'rank': rank,
        'certificate': certificate,
        'top_three': top_three,
    })
