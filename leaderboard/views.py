from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Max, Count
from django.utils import timezone
from django.core.cache import cache
from django.core.paginator import Paginator
from datetime import timedelta
from typing_practice.models import UserResult
from django.contrib.auth.models import User
from accounts.models import UserProfile
import logging

logger = logging.getLogger('typing_platform')


@login_required
def index(request):
    period = request.GET.get('period', 'all')
    leaderboard_type = request.GET.get('type', 'wpm')
    page_number = request.GET.get('page', 1)
    
    # Validate inputs
    if period not in ['all', 'week', 'month']:
        period = 'all'
    if leaderboard_type not in ['wpm', 'code_wpm', 'accuracy']:
        leaderboard_type = 'wpm'
    
    try:
        page_number = int(page_number)
    except (ValueError, TypeError):
        page_number = 1
    
    # Cache key
    cache_key = f'leaderboard_{period}_{leaderboard_type}'
    leaderboard_data = cache.get(cache_key)
    
    if leaderboard_data is None:
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
        
        # Helper function to build leaderboard data
        def build_leaderboard_data(user_stats, include_accuracy=False):
            """Build leaderboard data from user stats with batch profile lookup"""
            if not user_stats:
                return []
            
            # Get all user IDs for batch profile lookup
            user_ids = [stat['user__id'] for stat in user_stats]
            profiles = {p.user_id: p for p in UserProfile.objects.filter(user_id__in=user_ids)}
            users = {u.id: u for u in User.objects.filter(id__in=user_ids)}
            
            leaderboard_data = []
            for i, stat in enumerate(user_stats, 1):
                user_id = stat['user__id']
                profile = profiles.get(user_id)
                user = users.get(user_id)
                
                user_image = profile.image.url if profile and profile.image else None
                full_name = user.get_full_name() if user and user.get_full_name() else None
                
                entry = {
                    'rank': i,
                    'username': stat['user__username'],
                    'user_id': user_id,
                    'full_name': full_name,
                    'first_name': stat['user__first_name'],
                    'last_name': stat['user__last_name'],
                    'image': user_image,
                    'sessions': stat['total_sessions']
                }
                
                if include_accuracy:
                    entry['accuracy'] = round(stat['avg_accuracy'] or 0, 2)
                else:
                    entry['wpm'] = round(stat['max_wpm'] or 0, 2)
                    entry['avg_wpm'] = round(stat['avg_wpm'] or 0, 2)
                
                leaderboard_data.append(entry)
            
            return leaderboard_data
        
        # Get leaderboard based on type with optimized query
        if leaderboard_type == 'wpm':
            # Overall WPM leaderboard
            user_stats = results.values('user__username', 'user__id', 'user__first_name', 'user__last_name').annotate(
                avg_wpm=Avg('wpm'),
                max_wpm=Max('wpm'),
                total_sessions=Count('id')
            ).order_by('-max_wpm')
            
            leaderboard_data = build_leaderboard_data(user_stats, include_accuracy=False)
        
        elif leaderboard_type == 'code_wpm':
            # Code WPM leaderboard
            code_results = results.filter(session_type='code')
            user_stats = code_results.values('user__username', 'user__id', 'user__first_name', 'user__last_name').annotate(
                avg_wpm=Avg('wpm'),
                max_wpm=Max('wpm'),
                total_sessions=Count('id')
            ).order_by('-max_wpm')
            
            leaderboard_data = build_leaderboard_data(user_stats, include_accuracy=False)
        
        else:  # accuracy
            # Accuracy leaderboard
            user_stats = results.values('user__username', 'user__id', 'user__first_name', 'user__last_name').annotate(
                avg_accuracy=Avg('accuracy'),
                total_sessions=Count('id')
            ).filter(total_sessions__gte=5).order_by('-avg_accuracy')
            
            leaderboard_data = build_leaderboard_data(user_stats, include_accuracy=True)
        
        # Cache for 5 minutes
        cache.set(cache_key, leaderboard_data, 300)
    
    # Get user's rank
    user_rank = None
    for i, entry in enumerate(leaderboard_data, 1):
        if entry['username'] == request.user.username:
            user_rank = i
            break
    
    # Pagination - 30 users per page
    paginator = Paginator(leaderboard_data, 30)
    page_obj = paginator.get_page(page_number)
    
    # Social comparison data
    user_stats = None
    if user_rank:
        # Get user's stats for comparison
        user_results = UserResult.objects.filter(user=request.user)
        if period == 'week':
            start_date = timezone.now() - timedelta(days=7)
            user_results = user_results.filter(time__gte=start_date)
        elif period == 'month':
            start_date = timezone.now() - timedelta(days=30)
            user_results = user_results.filter(time__gte=start_date)
        
        user_stats = user_results.aggregate(
            avg_wpm=Avg('wpm'),
            max_wpm=Max('wpm'),
            avg_accuracy=Avg('accuracy'),
            total_sessions=Count('id')
        )
        
        # Compare with top 3
        top_3 = list(leaderboard_data[:3]) if len(leaderboard_data) >= 3 else list(leaderboard_data)
        comparison_data = []
        for entry in top_3:
            if entry['username'] != request.user.username:
                wpm_diff = 0
                if user_stats and 'max_wpm' in user_stats and user_stats['max_wpm']:
                    wpm_diff = entry.get('wpm', 0) - (user_stats['max_wpm'] or 0)
                comparison_data.append({
                    'username': entry['username'],
                    'wpm': entry.get('wpm', 0),
                    'accuracy': entry.get('accuracy', 0),
                    'wpm_diff': round(wpm_diff, 1),
                })
    else:
        comparison_data = None
    
    context = {
        'leaderboard_data': page_obj,
        'period': period,
        'leaderboard_type': leaderboard_type,
        'user_rank': user_rank,
        'page_obj': page_obj,
        'user_stats': user_stats,
        'comparison_data': comparison_data,
    }
    
    return render(request, 'leaderboard/index.html', context)
