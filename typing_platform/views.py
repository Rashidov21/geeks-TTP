from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Max, Count
from typing_practice.models import UserResult
from competitions.models import Competition, CompetitionParticipant


def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'home.html')


@login_required
def dashboard(request):
    user = request.user
    
    # Get user statistics
    results = UserResult.objects.filter(user=user)
    
    # Overall stats
    avg_wpm = results.aggregate(avg=Avg('wpm'))['avg'] or 0
    max_wpm = results.aggregate(max=Max('wpm'))['max'] or 0
    avg_accuracy = results.aggregate(avg=Avg('accuracy'))['avg'] or 0
    total_sessions = results.count()
    
    # Recent results
    recent_results = results[:10]
    
    # Competition invitations
    user_competitions = CompetitionParticipant.objects.filter(
        user=user,
        is_finished=False
    ).select_related('competition')
    
    # Pending competitions
    pending_competitions = Competition.objects.filter(
        participants=user,
        status='pending'
    )
    
    context = {
        'avg_wpm': round(avg_wpm, 2),
        'max_wpm': round(max_wpm, 2),
        'avg_accuracy': round(avg_accuracy, 2),
        'total_sessions': total_sessions,
        'recent_results': recent_results,
        'user_competitions': user_competitions,
        'pending_competitions': pending_competitions,
    }
    
    return render(request, 'dashboard.html', context)

