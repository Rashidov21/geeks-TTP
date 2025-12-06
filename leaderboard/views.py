from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Max, Count
from django.utils import timezone
from datetime import timedelta
from typing_practice.models import UserResult
from django.contrib.auth.models import User


@login_required
def index(request):
    period = request.GET.get('period', 'all')
    leaderboard_type = request.GET.get('type', 'wpm')
    
    # Calculate date range
    if period == 'week':
        start_date = timezone.now() - timedelta(days=7)
    elif period == 'month':
        start_date = timezone.now() - timedelta(days=30)
    else:
        start_date = None
    
    # Filter results
    if start_date:
        results = UserResult.objects.filter(time__gte=start_date)
    else:
        results = UserResult.objects.all()
    
    # Get leaderboard based on type
    if leaderboard_type == 'wpm':
        # Overall WPM leaderboard
        user_stats = results.values('user__username', 'user__id').annotate(
            avg_wpm=Avg('wpm'),
            max_wpm=Max('wpm'),
            total_sessions=Count('id')
        ).order_by('-max_wpm')[:100]
        
        leaderboard_data = []
        for i, stat in enumerate(user_stats, 1):
            leaderboard_data.append({
                'rank': i,
                'username': stat['user__username'],
                'wpm': round(stat['max_wpm'], 2),
                'avg_wpm': round(stat['avg_wpm'], 2),
                'sessions': stat['total_sessions']
            })
    
    elif leaderboard_type == 'code_wpm':
        # Code WPM leaderboard
        code_results = results.filter(session_type='code')
        user_stats = code_results.values('user__username', 'user__id').annotate(
            avg_wpm=Avg('wpm'),
            max_wpm=Max('wpm'),
            total_sessions=Count('id')
        ).order_by('-max_wpm')[:100]
        
        leaderboard_data = []
        for i, stat in enumerate(user_stats, 1):
            leaderboard_data.append({
                'rank': i,
                'username': stat['user__username'],
                'wpm': round(stat['max_wpm'], 2),
                'avg_wpm': round(stat['avg_wpm'], 2),
                'sessions': stat['total_sessions']
            })
    
    else:  # accuracy
        # Accuracy leaderboard
        user_stats = results.values('user__username', 'user__id').annotate(
            avg_accuracy=Avg('accuracy'),
            total_sessions=Count('id')
        ).filter(total_sessions__gte=5).order_by('-avg_accuracy')[:100]
        
        leaderboard_data = []
        for i, stat in enumerate(user_stats, 1):
            leaderboard_data.append({
                'rank': i,
                'username': stat['user__username'],
                'accuracy': round(stat['avg_accuracy'], 2),
                'sessions': stat['total_sessions']
            })
    
    # Get user's rank
    user_rank = None
    for i, entry in enumerate(leaderboard_data, 1):
        if entry['username'] == request.user.username:
            user_rank = i
            break
    
    context = {
        'leaderboard_data': leaderboard_data,
        'period': period,
        'leaderboard_type': leaderboard_type,
        'user_rank': user_rank,
    }
    
    return render(request, 'leaderboard/index.html', context)
