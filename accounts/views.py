from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.db.models import Avg, Max, Count, Sum
from django.utils import timezone
from django.utils.safestring import mark_safe
from datetime import timedelta
from collections import defaultdict
import json
from .models import UserProfile, UserLevel, UserBadge, Notification
from .forms import CustomUserCreationForm, CustomAuthenticationForm, UserProfileForm
from typing_practice.models import UserResult
from competitions.models import CompetitionParticipant


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create user profile (signal will handle it, but ensure it exists)
            UserProfile.objects.get_or_create(user=user, defaults={'is_manager': False})
            username = form.cleaned_data.get('username')
            messages.success(request, f'Hisob muvaffaqiyatli yaratildi, {username}!')
            login(request, user)
            return redirect('dashboard')
        else:
            # Convert form errors to Uzbek
            for field, errors in form.errors.items():
                for error in errors:
                    if 'password' in field.lower():
                        if 'too short' in error.lower() or 'qisqa' in error.lower():
                            messages.error(request, 'Parol kamida 8 belgidan iborat bo\'lishi kerak.')
                        elif 'too common' in error.lower() or 'oddiy' in error.lower():
                            messages.error(request, 'Parol juda oddiy. Boshqa parol tanlang.')
                        elif 'entirely numeric' in error.lower() or 'raqam' in error.lower():
                            messages.error(request, 'Parol to\'liq raqamlardan iborat bo\'lmasligi kerak.')
                        elif 'mismatch' in error.lower() or 'mos kelmaydi' in error.lower():
                            messages.error(request, 'Parollar mos kelmaydi.')
                        else:
                            messages.error(request, error)
                    elif 'username' in field.lower():
                        if 'already exists' in error.lower() or 'mavjud' in error.lower():
                            messages.error(request, 'Bu foydalanuvchi nomi allaqachon mavjud.')
                        else:
                            messages.error(request, error)
                    else:
                        messages.error(request, error)
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                if user.is_active:
                    login(request, user)
                    messages.success(request, f'Xush kelibsiz, {username}!')
                    return redirect('dashboard')
                else:
                    messages.error(request, 'Bu hisob faol emas.')
            else:
                messages.error(request, 'Foydalanuvchi nomi yoki parol noto\'g\'ri.')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    if 'invalid_login' in error.lower() or 'noto\'g\'ri' in error.lower():
                        messages.error(request, 'Foydalanuvchi nomi yoki parol noto\'g\'ri.')
                    elif 'inactive' in error.lower() or 'faol emas' in error.lower():
                        messages.error(request, 'Bu hisob faol emas.')
                    else:
                        messages.error(request, error)
    else:
        form = CustomAuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})


@login_required
def profile_view(request, user_id=None):
    """View user profile with analytics"""
    if user_id:
        profile_user = get_object_or_404(User, id=user_id)
    else:
        profile_user = request.user
    
    profile = get_object_or_404(UserProfile, user=profile_user)
    
    # Get user statistics
    user_results = UserResult.objects.filter(user=profile_user)
    
    # Overall stats
    total_sessions = user_results.count()
    avg_wpm = user_results.aggregate(avg=Avg('wpm'))['avg'] or 0
    max_wpm = user_results.aggregate(max=Max('wpm'))['max'] or 0
    avg_accuracy = user_results.aggregate(avg=Avg('accuracy'))['avg'] or 0
    
    # Text vs Code stats
    text_results = user_results.filter(session_type='text')
    code_results = user_results.filter(session_type='code')
    
    text_avg_wpm = text_results.aggregate(avg=Avg('wpm'))['avg'] or 0
    code_avg_wpm = code_results.aggregate(avg=Avg('wpm'))['avg'] or 0
    
    # Recent activity (last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_results = user_results.filter(time__gte=thirty_days_ago)
    recent_sessions = recent_results.count()
    
    # Best performance
    best_result = user_results.order_by('-wpm').first()
    
    # Progress over time (last 10 results)
    recent_10 = user_results.order_by('-time')[:10]

    # Certificates (top 3 in finished competitions with certificates enabled)
    # Optimized query to avoid N+1 problem
    certificate_awards = []
    participant_competitions = CompetitionParticipant.objects.filter(
        user=profile_user,
        competition__status='finished',
        competition__enable_certificates=True,
        is_finished=True
    ).select_related('competition').order_by('-result_wpm')
    
    # Get all competition IDs for batch processing
    competition_ids = [cp.competition_id for cp in participant_competitions]
    
    if competition_ids:
        # Get all winners for these competitions in one query
        all_winners = CompetitionParticipant.objects.filter(
            competition_id__in=competition_ids,
            is_finished=True
        ).select_related('user', 'competition').order_by('competition_id', '-result_wpm')
        
        # Group winners by competition
        winners_by_competition = {}
        for winner in all_winners:
            comp_id = winner.competition_id
            if comp_id not in winners_by_competition:
                winners_by_competition[comp_id] = []
            winners_by_competition[comp_id].append(winner)
        
        # Calculate ranks efficiently
        for cp in participant_competitions:
            comp_id = cp.competition_id
            winners = winners_by_competition.get(comp_id, [])
            
            rank = None
            for idx, winner in enumerate(winners, 1):
                if winner.user_id == profile_user.id:
                    rank = idx
                    break
            
            if rank and rank <= 3:
                certificate_awards.append({
                    'competition': cp.competition,
                    'rank': rank,
                    'result_wpm': cp.result_wpm,
                    'accuracy': cp.accuracy,
                })
    
    # Gamification data
    level_info, _ = UserLevel.objects.get_or_create(user=profile_user)
    earned_badges = UserBadge.objects.filter(user=profile_user).select_related('badge').order_by('-earned_at')
    all_badges = UserBadge.objects.filter(user=profile_user).select_related('badge')
    
    # Progress data (last 30 days, grouped by date)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    progress_results = list(user_results.filter(time__gte=thirty_days_ago).order_by('time')[:30])
    # Group by date and calculate average for same dates
    wpm_by_date = defaultdict(list)
    accuracy_by_date = defaultdict(list)
    for r in progress_results:
        date_str = r.time.strftime('%d.%m')
        wpm_by_date[date_str].append(float(r.wpm))
        accuracy_by_date[date_str].append(float(r.accuracy))
    
    wpm_progress = [{'date': date, 'wpm': sum(wpms) / len(wpms)} for date, wpms in wpm_by_date.items()]
    accuracy_progress = [{'date': date, 'accuracy': sum(accs) / len(accs)} for date, accs in accuracy_by_date.items()]
    
    context = {
        'profile_user': profile_user,
        'profile': profile,
        'total_sessions': total_sessions,
        'avg_wpm': round(avg_wpm, 2),
        'max_wpm': round(max_wpm, 2),
        'avg_accuracy': round(avg_accuracy, 2),
        'text_avg_wpm': round(text_avg_wpm, 2),
        'code_avg_wpm': round(code_avg_wpm, 2),
        'recent_sessions': recent_sessions,
        'best_result': best_result,
        'recent_10': recent_10,
        'is_own_profile': profile_user == request.user,
        'certificate_awards': certificate_awards,
        # Gamification
        'level_info': level_info,
        'earned_badges': earned_badges,
        'all_badges': all_badges,
        'wpm_progress': wpm_progress,  # Pass as list, not JSON string
        'accuracy_progress': accuracy_progress,  # Pass as list, not JSON string
    }
    
    return render(request, 'accounts/profile.html', context)


@login_required
def profile_edit(request):
    """Edit user profile"""
    profile = get_object_or_404(UserProfile, user=request.user)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            # Save profile
            form.save()
            # Update user's first_name and last_name
            user = request.user
            user.first_name = form.cleaned_data.get('first_name', '')
            user.last_name = form.cleaned_data.get('last_name', '')
            user.save()
            messages.success(request, 'Profil muvaffaqiyatli yangilandi!')
            return redirect('accounts:profile')
    else:
        form = UserProfileForm(instance=profile)
    
    return render(request, 'accounts/profile_edit.html', {'form': form})


@login_required
def notifications_view(request):
    """View all notifications"""
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:50]
    unread_count = Notification.get_unread_count(request.user)
    
    context = {
        'notifications': notifications,
        'unread_count': unread_count,
    }
    
    return render(request, 'accounts/notifications.html', context)


@login_required
def mark_notification_read(request, notification_id):
    """Mark notification as read"""
    from django.http import JsonResponse
    try:
        notification = Notification.objects.get(id=notification_id, user=request.user)
        notification.is_read = True
        notification.save()
        return JsonResponse({'success': True})
    except Notification.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Notification not found'}, status=404)


@login_required
def mark_all_notifications_read(request):
    """Mark all notifications as read"""
    from django.http import JsonResponse
    count = Notification.mark_all_read(request.user)
    return JsonResponse({'success': True, 'count': count})

