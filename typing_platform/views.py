from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Max, Count
from django.core.cache import cache
from django.core.paginator import Paginator
from typing_practice.models import UserResult
from competitions.models import Competition, CompetitionParticipant
import logging

logger = logging.getLogger('typing_platform')


def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'home.html')


@login_required
def dashboard(request):
    user = request.user
    
    # Try to get cached stats
    cache_key = f'user_stats_{user.id}'
    cached_stats = cache.get(cache_key)
    
    if cached_stats:
        stats = cached_stats
    else:
        # Get user statistics with optimized query
        results = UserResult.objects.filter(user=user)
        
        # Single aggregate query for all stats
        stats = results.aggregate(
            avg_wpm=Avg('wpm'),
            max_wpm=Max('wpm'),
            avg_accuracy=Avg('accuracy'),
            total_sessions=Count('id')
        )
        
        # Cache for 1 minute
        cache.set(cache_key, stats, 60)
    
    # Recent results with pagination
    results = UserResult.objects.filter(user=user).select_related('text', 'code_snippet')[:10]
    
    # Competition invitations with optimized queries
    user_competitions = CompetitionParticipant.objects.filter(
        user=user,
        is_finished=False
    ).select_related('competition', 'competition__created_by').order_by('-competition__start_time')[:5]
    
    # Pending competitions
    pending_competitions = Competition.objects.filter(
        participants=user,
        status='pending'
    ).select_related('created_by').order_by('start_time')[:5]
    
    context = {
        'avg_wpm': round(stats.get('avg_wpm') or 0, 2),
        'max_wpm': round(stats.get('max_wpm') or 0, 2),
        'avg_accuracy': round(stats.get('avg_accuracy') or 0, 2),
        'total_sessions': stats.get('total_sessions') or 0,
        'recent_results': results,
        'user_competitions': user_competitions,
        'pending_competitions': pending_competitions,
    }
    
    return render(request, 'dashboard.html', context)

