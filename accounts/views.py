from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.db.models import Avg, Max, Count, Sum
from django.utils import timezone
from datetime import timedelta
from .models import UserProfile
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
    certificate_awards = []
    participant_competitions = CompetitionParticipant.objects.filter(
        user=profile_user,
        competition__status='finished',
        competition__enable_certificates=True
    ).select_related('competition')
    
    for cp in participant_competitions:
        winners = CompetitionParticipant.objects.filter(
            competition=cp.competition,
            is_finished=True
        ).select_related('user').order_by('-result_wpm')
        
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

