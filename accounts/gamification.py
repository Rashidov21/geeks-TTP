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
        
        # Get user stats (yaxshilangan)
        stats = user_results.aggregate(
            total_sessions=Count('id'),
            max_wpm=Max('wpm'),
            avg_wpm=Avg('wpm'),
            avg_accuracy=Avg('accuracy'),
            text_sessions=Count('id', filter=Q(session_type='text')),
            code_sessions=Count('id', filter=Q(session_type='code')),
            perfect_sessions=Count('id', filter=Q(accuracy=100)),
            high_accuracy_sessions=Count('id', filter=Q(accuracy__gte=95)),
        )
        
        # Competition stats
        try:
            from competitions.models import CompetitionParticipant
            comp_stats = CompetitionParticipant.objects.filter(user=user).aggregate(
                total_participations=Count('id'),
                finished_competitions=Count('id', filter=Q(is_finished=True)),
            )
        except ImportError:
            comp_stats = {'total_participations': 0, 'finished_competitions': 0}
        
        # Battle stats
        try:
            from battles.models import BattleParticipant
            battle_stats = BattleParticipant.objects.filter(
                user=user,
                is_finished=True
            ).aggregate(
                total_battles=Count('id'),
                wins=Count('id', filter=Q(battle__winner=user)),
            )
        except ImportError:
            battle_stats = {'total_battles': 0, 'wins': 0}
        
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
                elif 'perfect_sessions' in req:
                    if stats['perfect_sessions'] and stats['perfect_sessions'] >= req['perfect_sessions']:
                        earned = True
                    else:
                        progress = int((stats['perfect_sessions'] or 0) / req['perfect_sessions'] * 100) if req['perfect_sessions'] > 0 else 0
                        
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
            
            elif badge.badge_type == 'competition':
                if 'first_place' in req:
                    # Check if user has first place in any competition
                    # Simplified: check if user has highest result_wpm in any competition
                    try:
                        from competitions.models import CompetitionParticipant
                        first_places = CompetitionParticipant.objects.filter(
                            user=user,
                            is_finished=True
                        ).order_by('-result_wpm').first()
                        if first_places and first_places.result_wpm:
                            # Check if this is the highest in that competition
                            competition = first_places.competition
                            highest = CompetitionParticipant.objects.filter(
                                competition=competition,
                                is_finished=True
                            ).order_by('-result_wpm').first()
                            if highest and highest.user == user:
                                earned = True
                    except:
                        pass
                    progress = 0
                elif 'second_place' in req:
                    # Similar logic for second place
                    progress = 0
                elif 'third_place' in req:
                    # Similar logic for third place
                    progress = 0
                elif 'participations' in req:
                    if comp_stats['total_participations'] >= req['participations']:
                        earned = True
                    else:
                        progress = int((comp_stats['total_participations'] / req['participations']) * 100) if req['participations'] > 0 else 0
                elif 'wins' in req:
                    # Simplified: count finished competitions as wins for now
                    wins = comp_stats['finished_competitions']
                    if wins >= req['wins']:
                        earned = True
                    else:
                        progress = int((wins / req['wins']) * 100) if req['wins'] > 0 else 0
            
            elif badge.badge_type == 'battle':
                if 'battle_wins' in req:
                    if battle_stats['wins'] and battle_stats['wins'] >= req['battle_wins']:
                        earned = True
                    else:
                        progress = int((battle_stats['wins'] or 0) / req['battle_wins'] * 100) if req['battle_wins'] > 0 else 0
                elif 'battles' in req:
                    if battle_stats['total_battles'] and battle_stats['total_battles'] >= req['battles']:
                        earned = True
                    else:
                        progress = int((battle_stats['total_battles'] or 0) / req['battles'] * 100) if req['battles'] > 0 else 0
            
            elif badge.badge_type == 'special':
                # Special badges require custom logic
                if 'perfect_week' in req:
                    # Check if user completed all daily challenges in a week
                    try:
                        from .models import ChallengeCompletion, DailyChallenge
                        from datetime import timedelta
                        today = timezone.now().date()
                        week_start = today - timedelta(days=7)
                        week_challenges = DailyChallenge.objects.filter(date__gte=week_start, date__lte=today)
                        completed = ChallengeCompletion.objects.filter(
                            user=user,
                            challenge__in=week_challenges
                        ).count()
                        if completed >= week_challenges.count() and week_challenges.count() >= 7:
                            earned = True
                    except:
                        pass
                    progress = 0
                elif 'early_completion' in req:
                    # Check early morning completions (before 10 AM)
                    # This would need to be tracked separately
                    progress = 0
                elif 'late_completion' in req:
                    # Check late night completions (after 10 PM)
                    # This would need to be tracked separately
                    progress = 0
                elif 'comebacks' in req:
                    # Track streak breaks and restarts
                    # This would need to be tracked separately
                    progress = 0
            
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
                    user_badge.update_progress(min(100, progress))
        
        return None
        
    except Exception as e:
        logger.error(f"Error checking badges for user {user.username}: {e}", exc_info=True)
        return None


def calculate_xp_for_result(result):
    """Calculate XP reward for a practice result with improved multipliers"""
    base_xp = 10
    
    # Performance multipliers
    wpm_multiplier = 1.0
    if result.wpm >= 150:
        wpm_multiplier = 3.0
    elif result.wpm >= 120:
        wpm_multiplier = 2.5
    elif result.wpm >= 100:
        wpm_multiplier = 2.0
    elif result.wpm >= 80:
        wpm_multiplier = 1.5
    elif result.wpm >= 60:
        wpm_multiplier = 1.2
    
    accuracy_multiplier = 1.0
    if result.accuracy >= 100:
        accuracy_multiplier = 2.0
    elif result.accuracy >= 98:
        accuracy_multiplier = 1.5
    elif result.accuracy >= 95:
        accuracy_multiplier = 1.3
    elif result.accuracy >= 90:
        accuracy_multiplier = 1.1
    
    # Streak bonus
    try:
        profile = UserProfile.objects.get(user=result.user)
        streak_bonus = min(profile.current_streak * 0.1, 1.0)  # Max 100% bonus
    except:
        streak_bonus = 0
    
    # Session type bonus
    session_bonus = 1.2 if result.session_type == 'code' else 1.0
    
    # Calculate total XP
    total_xp = int(base_xp * wpm_multiplier * accuracy_multiplier * (1 + streak_bonus) * session_bonus)
    
    # Record bonus (if this is a new personal best)
    user_results = UserResult.objects.filter(user=result.user)
    max_wpm = user_results.aggregate(max_wpm=Max('wpm'))['max_wpm']
    if result.wpm == max_wpm and result.wpm > 0:
        total_xp += 50  # New record!
    
    return total_xp


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

