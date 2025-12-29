"""
Gamification utilities for badges, XP, streaks, etc.
"""
from django.utils import timezone
from datetime import timedelta, date
from django.db.models import Count, Max, Avg, Q
from typing_practice.models import UserResult
from .models import UserProfile, Badge, UserBadge, UserLevel, DailyChallenge, ChallengeCompletion, Notification
import random
import logging

logger = logging.getLogger('typing_platform')


def update_streak(user):
    """Update user's streak based on practice history"""
    try:
        profile = UserProfile.objects.get(user=user)
        today = timezone.now().date()
        
        # Get last practice date
        last_result = UserResult.objects.filter(user=user).order_by('-date').first()
        
        if not last_result:
            profile.current_streak = 0
            profile.last_practice_date = None
            profile.save()
            return
        
        last_practice = last_result.date
        
        # Check if user practiced today
        if last_practice == today:
            # Already practiced today, check if streak should continue
            if profile.last_practice_date == today:
                # Already updated today
                return
            
            # Check if yesterday was practiced (streak continues)
            yesterday = today - timedelta(days=1)
            if profile.last_practice_date == yesterday:
                profile.current_streak += 1
            elif profile.last_practice_date != today:
                # New streak starting
                profile.current_streak = 1
            
            profile.last_practice_date = today
            profile.total_practice_days += 1
            
            # Update longest streak
            if profile.current_streak > profile.longest_streak:
                profile.longest_streak = profile.current_streak
            
            profile.save()
        elif last_practice < today - timedelta(days=1):
            # Streak broken
            profile.current_streak = 0
            profile.last_practice_date = last_practice
            profile.save()
            
    except UserProfile.DoesNotExist:
        logger.warning(f"UserProfile not found for user {user.username}")
    except Exception as e:
        logger.error(f"Error updating streak for user {user.username}: {e}", exc_info=True)


def check_and_award_badges(user, result=None):
    """Check if user qualifies for any badges and award them"""
    try:
        profile = UserProfile.objects.get(user=user)
        user_results = UserResult.objects.filter(user=user)
        
        # Get user stats
        stats = user_results.aggregate(
            total_sessions=Count('id'),
            max_wpm=Max('wpm'),
            avg_accuracy=Avg('accuracy'),
            text_sessions=Count('id', filter=Q(session_type='text')),
            code_sessions=Count('id', filter=Q(session_type='code')),
        )
        
        # Get active badges
        badges = Badge.objects.filter(is_active=True)
        
        for badge in badges:
            # Skip if already earned
            if UserBadge.objects.filter(user=user, badge=badge).exists():
                continue
            
            # Check requirements
            req = badge.requirement
            earned = False
            progress = 0
            
            if badge.badge_type == 'speed':
                if 'wpm' in req:
                    if stats['max_wpm'] and stats['max_wpm'] >= req['wpm']:
                        earned = True
                    else:
                        progress = int((stats['max_wpm'] or 0) / req['wpm'] * 100) if req['wpm'] > 0 else 0
                        
            elif badge.badge_type == 'accuracy':
                if 'accuracy' in req:
                    if stats['avg_accuracy'] and stats['avg_accuracy'] >= req['accuracy']:
                        earned = True
                    else:
                        progress = int((stats['avg_accuracy'] or 0) / req['accuracy'] * 100) if req['accuracy'] > 0 else 0
                        
            elif badge.badge_type == 'streak':
                if 'days' in req:
                    if profile.current_streak >= req['days']:
                        earned = True
                    else:
                        progress = int((profile.current_streak / req['days']) * 100) if req['days'] > 0 else 0
                        
            elif badge.badge_type == 'milestone':
                if 'sessions' in req:
                    if stats['total_sessions'] >= req['sessions']:
                        earned = True
                    else:
                        progress = int((stats['total_sessions'] / req['sessions']) * 100) if req['sessions'] > 0 else 0
                elif 'text_sessions' in req:
                    if stats['text_sessions'] >= req['text_sessions']:
                        earned = True
                    else:
                        progress = int((stats['text_sessions'] / req['text_sessions']) * 100) if req['text_sessions'] > 0 else 0
                elif 'code_sessions' in req:
                    if stats['code_sessions'] >= req['code_sessions']:
                        earned = True
                    else:
                        progress = int((stats['code_sessions'] / req['code_sessions']) * 100) if req['code_sessions'] > 0 else 0
                        
            elif badge.badge_type == 'consistency':
                if 'practice_days' in req:
                    if profile.total_practice_days >= req['practice_days']:
                        earned = True
                    else:
                        progress = int((profile.total_practice_days / req['practice_days']) * 100) if req['practice_days'] > 0 else 0
            
            # Award badge if earned
            if earned:
                UserBadge.objects.get_or_create(
                    user=user,
                    badge=badge,
                    defaults={'progress': 100}
                )
                
                # Award XP
                level_info, created = UserLevel.objects.get_or_create(user=user)
                level_up, new_level = level_info.add_xp(badge.xp_reward)
                
                # Create notification
                Notification.objects.create(
                    user=user,
                    notification_type='badge',
                    title=f'Yangi badge: {badge.name}',
                    message=f'{badge.icon} {badge.description}',
                    icon=badge.icon,
                    link='/accounts/profile/'
                )
                
                # Notify level up if happened
                if level_up:
                    Notification.objects.create(
                        user=user,
                        notification_type='level_up',
                        title=f'Level {new_level} ga yetdingiz!',
                        message=f'🎉 Tabriklaymiz! Siz Level {new_level} ga yetdingiz!',
                        icon='🎉',
                        link='/dashboard/'
                    )
                
                logger.info(f"Badge awarded: {user.username} earned {badge.name} (Level up: {level_up})")
                
                return {
                    'badge': badge,
                    'level_up': level_up,
                    'new_level': new_level,
                    'xp_gained': badge.xp_reward
                }
            else:
                # Update progress if badge not earned yet
                user_badge, created = UserBadge.objects.get_or_create(
                    user=user,
                    badge=badge,
                    defaults={'progress': progress}
                )
                if not created:
                    user_badge.progress = min(100, progress)
                    user_badge.save()
        
        return None
        
    except Exception as e:
        logger.error(f"Error checking badges for user {user.username}: {e}", exc_info=True)
        return None


def calculate_xp_for_result(result):
    """Calculate XP reward for a practice result"""
    base_xp = 10  # Base XP for completing a practice
    
    # Bonus XP for good performance
    bonus_xp = 0
    if result.wpm >= 100:
        bonus_xp += 50  # Elite speed
    elif result.wpm >= 80:
        bonus_xp += 25  # Expert speed
    elif result.wpm >= 60:
        bonus_xp += 10  # Advanced speed
    
    if result.accuracy >= 95:
        bonus_xp += 25  # Perfect accuracy
    elif result.accuracy >= 90:
        bonus_xp += 10  # High accuracy
    
    # Record bonus (if this is a new personal best)
    user_results = UserResult.objects.filter(user=result.user)
    max_wpm = user_results.aggregate(max_wpm=Max('wpm'))['max_wpm']
    if result.wpm == max_wpm and result.wpm > 0:
        bonus_xp += 50  # New record!
    
    return base_xp + bonus_xp


def award_xp_for_practice(user, result):
    """Award XP for completing a practice"""
    try:
        level_info, created = UserLevel.objects.get_or_create(user=user)
        xp_amount = calculate_xp_for_result(result)
        old_level = level_info.level
        level_up, new_level = level_info.add_xp(xp_amount)
        
        # Notify level up
        if level_up:
            Notification.objects.create(
                user=user,
                notification_type='level_up',
                title=f'Level {new_level} ga yetdingiz!',
                message=f'🎉 Tabriklaymiz! Siz Level {new_level} ga yetdingiz!',
                icon='🎉',
                link='/dashboard/'
            )
        
        # Check streak milestones
        profile = UserProfile.objects.get(user=user)
        if profile.current_streak in [7, 14, 30, 60, 100]:
            Notification.objects.create(
                user=user,
                notification_type='streak',
                title=f'{profile.current_streak} kun ketma-ketlik!',
                message=f'🔥 Ajoyib! Siz {profile.current_streak} kun ketma-ket mashq qildingiz!',
                icon='🔥',
                link='/accounts/profile/'
            )
        
        return {
            'xp_gained': xp_amount,
            'level_up': level_up,
            'new_level': new_level,
            'total_xp': level_info.total_xp,
            'current_xp': level_info.current_xp,
            'next_level_xp': level_info.get_xp_for_next_level()
        }
    except Exception as e:
        logger.error(f"Error awarding XP for user {user.username}: {e}", exc_info=True)
        return None


def check_daily_challenge(user, result):
    """Check if user completed today's challenge"""
    try:
        today = timezone.now().date()
        challenge, created = DailyChallenge.objects.get_or_create(
            date=today,
            defaults={
                'challenge_type': random.choice(['speed', 'accuracy', 'code', 'text']),
                'title': _generate_challenge_title(),
                'description': 'Bugungi vazifani bajarib, bonus XP oling!',
                'target_wpm': random.randint(40, 80),
                'target_accuracy': random.uniform(85, 95),
                'reward_xp': 50,
            }
        )
        
        # Skip if already completed
        if ChallengeCompletion.objects.filter(user=user, challenge=challenge).exists():
            return None
        
        completed = False
        
        if challenge.challenge_type == 'speed':
            if challenge.target_wpm and result.wpm >= challenge.target_wpm:
                completed = True
        elif challenge.challenge_type == 'accuracy':
            if challenge.target_accuracy and result.accuracy >= challenge.target_accuracy:
                completed = True
        elif challenge.challenge_type == 'code':
            if result.session_type == 'code':
                if challenge.target_wpm and result.wpm >= challenge.target_wpm:
                    completed = True
        elif challenge.challenge_type == 'text':
            if result.session_type == 'text':
                if challenge.target_wpm and result.wpm >= challenge.target_wpm:
                    completed = True
        
        if completed:
            # Award completion
            level_info, _ = UserLevel.objects.get_or_create(user=user)
            level_up, new_level = level_info.add_xp(challenge.reward_xp)
            
            ChallengeCompletion.objects.create(
                user=user,
                challenge=challenge,
                result_wpm=result.wpm,
                result_accuracy=result.accuracy,
                xp_earned=challenge.reward_xp
            )
            
            # Create notification
            Notification.objects.create(
                user=user,
                notification_type='challenge',
                title='Kunlik vazifa bajarildi!',
                message=f'✅ {challenge.title} - {challenge.reward_xp} XP olingiz!',
                icon='✅',
                link='/dashboard/'
            )
            
            logger.info(f"Challenge completed: {user.username} - {challenge.title}")
            
            return {
                'challenge': challenge,
                'xp_earned': challenge.reward_xp,
                'level_up': level_up,
                'new_level': new_level
            }
        
        return None
        
    except Exception as e:
        logger.error(f"Error checking challenge completion: {e}", exc_info=True)
        return None


def _generate_challenge_title():
    """Generate random challenge title"""
    titles = [
        "Bugun tezroq yozing!",
        "Aniqlikni yaxshilang!",
        "Kod yozishda ustunlik qiling!",
        "Matn mashqida rekord qo'ying!",
        "Bugun eng yaxshi natijangizni ko'rsating!",
    ]
    return random.choice(titles)

