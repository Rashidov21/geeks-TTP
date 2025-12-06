from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Avg
from .models import Competition, CompetitionParticipant, CompetitionStage, CompetitionParticipantStage
from typing_practice.models import Text, CodeSnippet
import json
import secrets
import random


@login_required
def competition_list(request):
    # Show all public competitions and user's competitions
    all_competitions = Competition.objects.filter(is_public=True).order_by('-start_time')
    user_competitions = Competition.objects.filter(participants=request.user).order_by('-start_time')
    
    return render(request, 'competitions/list.html', {
        'user_competitions': user_competitions,
        'all_competitions': all_competitions,
    })


@login_required
def competition_detail(request, competition_id):
    competition = get_object_or_404(Competition, id=competition_id)
    
    # Check if user can view (public or participant)
    if not competition.is_public and request.user not in competition.participants.all():
        if not request.user.userprofile.is_manager:
            messages.error(request, 'This competition is private')
            return redirect('competitions:list')
    
    participant = CompetitionParticipant.objects.filter(
        user=request.user,
        competition=competition
    ).first()
    
    # Get all participants with results
    participants = CompetitionParticipant.objects.filter(
        competition=competition
    ).order_by('-result_wpm')
    
    # Get stages
    stages = CompetitionStage.objects.filter(competition=competition).order_by('stage_number')
    
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
            status='pending'
        )
        
        # Create 3 stages with random texts/codes
        if mode == 'text':
            texts = list(Text.objects.filter(difficulty=difficulty).order_by('?'))
            if len(texts) >= 3:
                selected_texts = random.sample(texts, 3)
                for i, text in enumerate(selected_texts, 1):
                    CompetitionStage.objects.create(
                        competition=competition,
                        stage_number=i,
                        text=text
                    )
        elif mode == 'code':
            codes = list(CodeSnippet.objects.filter(difficulty=difficulty).order_by('?'))
            if len(codes) >= 3:
                selected_codes = random.sample(codes, 3)
                for i, code in enumerate(selected_codes, 1):
                    CompetitionStage.objects.create(
                        competition=competition,
                        stage_number=i,
                        code_snippet=code
                    )
        
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
    
    messages.success(request, 'Competition finished!')
    return redirect('competitions:results', competition_id=competition.id)


@login_required
def competition_play(request, competition_id, stage_number=1):
    competition = get_object_or_404(Competition, id=competition_id)
    participant = CompetitionParticipant.objects.filter(
        user=request.user,
        competition=competition
    ).first()
    
    if not participant:
        messages.error(request, 'You are not a participant in this competition')
        return redirect('competitions:detail', competition_id=competition.id)
    
    if competition.status != 'active':
        messages.error(request, 'Competition is not active')
        return redirect('competitions:detail', competition_id=competition.id)
    
    # Get current stage
    stage = get_object_or_404(CompetitionStage, competition=competition, stage_number=stage_number)
    
    # Get or create participant stage
    participant_stage, created = CompetitionParticipantStage.objects.get_or_create(
        participant=participant,
        stage=stage
    )
    
    if created and stage_number == 1:
        participant.started_at = timezone.now()
        participant.current_stage = 1
        participant.save()
    
    # Get all stages for navigation
    all_stages = CompetitionStage.objects.filter(competition=competition).order_by('stage_number')
    
    return render(request, 'competitions/play.html', {
        'competition': competition,
        'participant': participant,
        'stage': stage,
        'participant_stage': participant_stage,
        'stage_number': stage_number,
        'all_stages': all_stages,
    })


@login_required
@csrf_exempt
def competition_save_result(request, competition_id, stage_number):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        competition = get_object_or_404(Competition, id=competition_id)
        participant = CompetitionParticipant.objects.get(
            user=request.user,
            competition=competition
        )
        stage = get_object_or_404(CompetitionStage, competition=competition, stage_number=stage_number)
        
        data = json.loads(request.body)
        wpm = float(data.get('wpm', 0))
        accuracy = float(data.get('accuracy', 0))
        mistakes = int(data.get('mistakes', 0))
        
        # Save stage result
        participant_stage, created = CompetitionParticipantStage.objects.get_or_create(
            participant=participant,
            stage=stage
        )
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
        
        # Calculate average results
        stage_results = CompetitionParticipantStage.objects.filter(
            participant=participant,
            is_finished=True
        )
        if stage_results.exists():
            participant.result_wpm = stage_results.aggregate(avg=Avg('wpm'))['avg']
            participant.accuracy = stage_results.aggregate(avg=Avg('accuracy'))['avg']
            participant.mistakes = sum(sr.mistakes for sr in stage_results)
        
        participant.save()
        
        return JsonResponse({
            'success': True,
            'next_stage': stage_number + 1 if stage_number < 3 else None,
            'finished': stage_number >= 3
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
def competition_results(request, competition_id):
    competition = get_object_or_404(Competition, id=competition_id)
    
    # Check if user can view (public or participant)
    if not competition.is_public and request.user not in competition.participants.all():
        if not request.user.userprofile.is_manager:
            messages.error(request, 'This competition is private')
            return redirect('competitions:list')
    
    # Get all participants with stage results
    participants = CompetitionParticipant.objects.filter(
        competition=competition
    ).order_by('-result_wpm')
    
    # Get stages
    stages = CompetitionStage.objects.filter(competition=competition).order_by('stage_number')
    
    # Get stage results for each participant
    participant_results = {}
    for participant in participants:
        stage_results = CompetitionParticipantStage.objects.filter(
            participant=participant
        ).select_related('stage').order_by('stage__stage_number')
        participant_results[participant.id] = {
            'participant': participant,
            'stages': {}
        }
        for stage_result in stage_results:
            participant_results[participant.id]['stages'][stage_result.stage.stage_number] = stage_result
    
    return render(request, 'competitions/results.html', {
        'competition': competition,
        'participants': participants,
        'stages': stages,
        'participant_results': participant_results,
    })
