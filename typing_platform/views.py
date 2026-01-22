from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Max, Count
from django.core.cache import cache
from django.core.paginator import Paginator
from django.utils import timezone
from django.utils.safestring import mark_safe
import json
from collections import defaultdict
from typing_practice.models import UserResult
from competitions.models import Competition, CompetitionParticipant
from accounts.models import UserProfile, UserLevel, UserBadge, DailyChallenge, ChallengeCompletion, Notification
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
    
    # Gamification data
    profile = UserProfile.objects.get(user=user)
    level_info, _ = UserLevel.objects.get_or_create(user=user)
    earned_badges = UserBadge.objects.filter(user=user).select_related('badge').order_by('-earned_at')[:6]
    
    # Daily challenge
    today = timezone.now().date()
    today_challenge = DailyChallenge.objects.filter(date=today, is_active=True).first()
    challenge_completed = False
    if today_challenge:
        challenge_completed = ChallengeCompletion.objects.filter(user=user, challenge=today_challenge).exists()
    
    # Recent progress data (last 10 results, grouped by date)
    progress_data = UserResult.objects.filter(user=user).order_by('-time')[:10]
    # Group by date and calculate average for same dates
    wpm_by_date = defaultdict(list)
    accuracy_by_date = defaultdict(list)
    for r in reversed(progress_data):
        date_str = r.time.strftime('%d.%m')
        wpm_by_date[date_str].append(r.wpm)
        accuracy_by_date[date_str].append(r.accuracy)
    
    wpm_data = [{'date': date, 'wpm': sum(wpms) / len(wpms)} for date, wpms in wpm_by_date.items()]
    accuracy_data = [{'date': date, 'accuracy': sum(accs) / len(accs)} for date, accs in accuracy_by_date.items()]
    
    # Unread notifications count
    unread_notifications = Notification.get_unread_count(user)
    
    context = {
        'avg_wpm': round(stats.get('avg_wpm') or 0, 2),
        'max_wpm': round(stats.get('max_wpm') or 0, 2),
        'avg_accuracy': round(stats.get('avg_accuracy') or 0, 2),
        'total_sessions': stats.get('total_sessions') or 0,
        'recent_results': results,
        'user_competitions': user_competitions,
        'pending_competitions': pending_competitions,
        # Gamification
        'profile': profile,
        'level_info': level_info,
        'earned_badges': earned_badges,
        'today_challenge': today_challenge,
        'challenge_completed': challenge_completed,
        'wpm_data': wpm_data,  # Pass as list, not JSON string
        'accuracy_data': accuracy_data,  # Pass as list, not JSON string
        'unread_notifications': unread_notifications,
    }
    
    return render(request, 'dashboard.html', context)


def custom_404(request, exception):
    """Custom 404 page"""
    return render(request, '404.html', status=404)


def custom_500(request):
    """Custom 500 page"""
    return render(request, '500.html', status=500)


def privacy_policy(request):
    """Privacy Policy sahifasi"""
    return render(request, 'legal/privacy_policy.html')


def terms_of_service(request):
    """Terms of Service sahifasi"""
    return render(request, 'legal/terms_of_service.html')


def contact(request):
    """Contact sahifasi"""
    return render(request, 'legal/contact.html')

