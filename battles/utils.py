"""
Battle utilities: ELO calculation, rewards, matchmaking, etc.
"""
from django.utils import timezone
from django.core.cache import cache
from django.contrib.auth.models import User
from .models import Battle, BattleRating, BattleParticipant
from accounts.models import UserLevel, Notification, Badge, UserBadge
from accounts.gamification import calculate_xp_for_result
import logging
import time
import random

logger = logging.getLogger('typing_platform')

ONLINE_TIMEOUT = 300  # 5 daqiqa


def get_active_users():
    """Get list of currently active user IDs"""
    roster = cache.get("online-roster", [])
    now = int(time.time())
    active = []
    
    for uid in roster:
        timestamp = cache.get(f"online-user:{uid}")
        if timestamp and (now - timestamp) <= ONLINE_TIMEOUT:
            active.append(uid)
    
    return list(set(active))


def calculate_elo_rating(rating1, rating2, result1):
    """
    Calculate new ELO ratings after a battle.
    result1: 1 if player1 wins, 0.5 if draw, 0 if player1 loses
    """
    K = 32  # K-factor
    
    # Expected scores
    expected1 = 1 / (1 + 10 ** ((rating2 - rating1) / 400))
    expected2 = 1 / (1 + 10 ** ((rating1 - rating2) / 400))
    
    # New ratings
    new_rating1 = rating1 + K * (result1 - expected1)
    new_rating2 = rating2 + K * ((1 - result1) - expected2)
    
    return int(new_rating1), int(new_rating2)


def update_battle_ratings(battle):
    """Update ELO ratings after battle completion"""
    if battle.status != 'finished' or not battle.winner:
        return
    
    participants = battle.participants.all()
    if participants.count() != 2:
        return
    
    creator_participant = participants.filter(user=battle.creator).first()
    opponent_participant = participants.filter(user=battle.opponent).first()
    
    if not creator_participant or not opponent_participant:
        return
    
    # Get or create ratings
    creator_rating, _ = BattleRating.objects.get_or_create(user=battle.creator)
    opponent_rating, _ = BattleRating.objects.get_or_create(user=battle.opponent)
    
    # Determine result (1 = creator wins, 0 = opponent wins, 0.5 = draw)
    if battle.winner == battle.creator:
        result = 1.0
    elif battle.winner == battle.opponent:
        result = 0.0
    else:
        # Draw based on battle type
        if battle.battle_type == 'speed':
            # Higher WPM wins
            if creator_participant.wpm > opponent_participant.wpm:
                result = 1.0
            elif opponent_participant.wpm > creator_participant.wpm:
                result = 0.0
            else:
                result = 0.5
        elif battle.battle_type == 'accuracy':
            # Higher accuracy wins
            if creator_participant.accuracy > opponent_participant.accuracy:
                result = 1.0
            elif opponent_participant.accuracy > creator_participant.accuracy:
                result = 0.0
            else:
                result = 0.5
        else:
            # Balanced: WPM * accuracy
            creator_score = creator_participant.wpm * creator_participant.accuracy
            opponent_score = opponent_participant.wpm * opponent_participant.accuracy
            if creator_score > opponent_score:
                result = 1.0
            elif opponent_score > creator_score:
                result = 0.0
            else:
                result = 0.5
    
    # Calculate new ratings
    new_creator_rating, new_opponent_rating = calculate_elo_rating(
        creator_rating.rating,
        opponent_rating.rating,
        result
    )
    
    # Update creator rating
    creator_rating.rating = new_creator_rating
    creator_rating.total_battles += 1
    if result == 1.0:
        creator_rating.wins += 1
        creator_rating.win_streak += 1
        if creator_rating.win_streak > creator_rating.best_win_streak:
            creator_rating.best_win_streak = creator_rating.win_streak
        opponent_rating.losses += 1
        opponent_rating.win_streak = 0
    elif result == 0.0:
        creator_rating.losses += 1
        creator_rating.win_streak = 0
        opponent_rating.wins += 1
        opponent_rating.win_streak += 1
        if opponent_rating.win_streak > opponent_rating.best_win_streak:
            opponent_rating.best_win_streak = opponent_rating.win_streak
    else:
        creator_rating.draws += 1
        opponent_rating.draws += 1
        creator_rating.win_streak = 0
        opponent_rating.win_streak = 0
    
    # Update opponent rating
    opponent_rating.rating = new_opponent_rating
    opponent_rating.total_battles += 1
    
    creator_rating.save()
    opponent_rating.save()
    
    logger.info(f"Battle ratings updated: {battle.creator.username} ({new_creator_rating}), {battle.opponent.username} ({new_opponent_rating})")


def award_battle_rewards(battle):
    """Award XP and badges for battle completion"""
    if battle.status != 'finished':
        return
    
    participants = battle.participants.all()
    if participants.count() != 2:
        return
    
    creator_participant = participants.filter(user=battle.creator).first()
    opponent_participant = participants.filter(user=battle.opponent).first()
    
    if not creator_participant or not opponent_participant:
        return
    
    # Award XP
    winner_xp = 100
    loser_xp = 30
    draw_xp = 50
    
    if battle.winner == battle.creator:
        award_xp_to_user(battle.creator, winner_xp, "Battle g'olibi")
        award_xp_to_user(battle.opponent, loser_xp, "Battle mag'lubi")
    elif battle.winner == battle.opponent:
        award_xp_to_user(battle.opponent, winner_xp, "Battle g'olibi")
        award_xp_to_user(battle.creator, loser_xp, "Battle mag'lubi")
    else:
        award_xp_to_user(battle.creator, draw_xp, "Battle durang")
        award_xp_to_user(battle.opponent, draw_xp, "Battle durang")
    
    # Check for battle badges
    check_battle_badges(battle.creator, battle)
    check_battle_badges(battle.opponent, battle)


def award_xp_to_user(user, xp_amount, reason=""):
    """Award XP to user"""
    try:
        level_info, created = UserLevel.objects.get_or_create(user=user)
        old_level = level_info.level
        level_up, new_level = level_info.add_xp(xp_amount)
        
        if level_up:
            Notification.objects.create(
                user=user,
                notification_type='level_up',
                title=f'Level {new_level} ga yetdingiz!',
                message=f'🎉 {reason} uchun {xp_amount} XP oldingiz va Level {new_level} ga yetdingiz!',
                icon='🎉',
                link='/dashboard/'
            )
        else:
            Notification.objects.create(
                user=user,
                notification_type='achievement',
                title='XP olingiz!',
                message=f'✅ {reason} uchun {xp_amount} XP oldingiz!',
                icon='✅',
                link='/dashboard/'
            )
        
        logger.info(f"XP awarded: {user.username} - {xp_amount} XP ({reason})")
    except Exception as e:
        logger.error(f"Error awarding XP to {user.username}: {e}", exc_info=True)


def check_battle_badges(user, battle):
    """Check and award battle-related badges"""
    try:
        rating = BattleRating.objects.get(user=user)
        
        # Battle Winner badge (10 wins)
        if rating.wins >= 10:
            badge, created = Badge.objects.get_or_create(
                name="Battle Winner",
                defaults={
                    'description': '10 ta battle g\'alabasi',
                    'icon': '🏆',
                    'badge_type': 'competition',
                    'requirement': {'wins': 10},
                    'xp_reward': 200,
                }
            )
            if created or not UserBadge.objects.filter(user=user, badge=badge).exists():
                UserBadge.objects.get_or_create(user=user, badge=badge, defaults={'progress': 100})
                Notification.objects.create(
                    user=user,
                    notification_type='badge',
                    title='Yangi badge: Battle Winner',
                    message='🏆 10 ta battle g\'alabasi uchun badge oldingiz!',
                    icon='🏆',
                    link='/accounts/profile/'
                )
        
        # Undefeated badge (5 win streak)
        if rating.win_streak >= 5:
            badge, created = Badge.objects.get_or_create(
                name="Undefeated",
                defaults={
                    'description': '5 ketma-ket battle g\'alabasi',
                    'icon': '🔥',
                    'badge_type': 'streak',
                    'requirement': {'win_streak': 5},
                    'xp_reward': 150,
                }
            )
            if created or not UserBadge.objects.filter(user=user, badge=badge).exists():
                UserBadge.objects.get_or_create(user=user, badge=badge, defaults={'progress': 100})
                Notification.objects.create(
                    user=user,
                    notification_type='badge',
                    title='Yangi badge: Undefeated',
                    message='🔥 5 ketma-ket g\'alaba uchun badge oldingiz!',
                    icon='🔥',
                    link='/accounts/profile/'
                )
        
        # Comeback King badge (rating increased significantly)
        # This would need to track rating changes, simplified here
        
    except BattleRating.DoesNotExist:
        pass
    except Exception as e:
        logger.error(f"Error checking battle badges for {user.username}: {e}", exc_info=True)


def find_match_for_user(user, battle_mode='text', battle_type='balanced', time_limit=300):
    """Find a suitable opponent for auto-matchmaking"""
    active_user_ids = get_active_users()
    
    # Remove current user
    active_user_ids = [uid for uid in active_user_ids if uid != user.id]
    
    if not active_user_ids:
        return None
    
    # Get user's rating
    user_rating, _ = BattleRating.objects.get_or_create(user=user)
    
    # Find users with similar rating (±200 points)
    min_rating = user_rating.rating - 200
    max_rating = user_rating.rating + 200
    
    # Try to find user with similar rating
    similar_users = BattleRating.objects.filter(
        user_id__in=active_user_ids,
        rating__gte=min_rating,
        rating__lte=max_rating
    ).exclude(user=user).order_by('?')[:5]
    
    if similar_users.exists():
        opponent = similar_users.first().user
    else:
        # If no similar rating, pick random active user
        opponent = User.objects.filter(id__in=active_user_ids).exclude(id=user.id).order_by('?').first()
    
    return opponent


def determine_battle_winner(battle):
    """Determine winner based on battle type"""
    participants = battle.participants.filter(is_finished=True)
    if participants.count() != 2:
        return None
    
    creator_participant = participants.filter(user=battle.creator).first()
    opponent_participant = participants.filter(user=battle.opponent).first()
    
    if not creator_participant or not opponent_participant:
        return None
    
    if battle.battle_type == 'speed':
        # Highest WPM wins
        if creator_participant.wpm > opponent_participant.wpm:
            return battle.creator
        elif opponent_participant.wpm > creator_participant.wpm:
            return battle.opponent
        # Tie: higher accuracy wins
        elif creator_participant.accuracy > opponent_participant.accuracy:
            return battle.creator
        elif opponent_participant.accuracy > creator_participant.accuracy:
            return battle.opponent
        else:
            return None  # Draw
    
    elif battle.battle_type == 'accuracy':
        # Highest accuracy wins
        if creator_participant.accuracy > opponent_participant.accuracy:
            return battle.creator
        elif opponent_participant.accuracy > creator_participant.accuracy:
            return battle.opponent
        # Tie: higher WPM wins
        elif creator_participant.wpm > opponent_participant.wpm:
            return battle.creator
        elif opponent_participant.wpm > creator_participant.wpm:
            return battle.opponent
        else:
            return None  # Draw
    
    elif battle.battle_type == 'endurance':
        # Lower mistakes wins (endurance = consistency)
        if creator_participant.mistakes < opponent_participant.mistakes:
            return battle.creator
        elif opponent_participant.mistakes < creator_participant.mistakes:
            return battle.opponent
        # Tie: higher WPM wins
        elif creator_participant.wpm > opponent_participant.wpm:
            return battle.creator
        elif opponent_participant.wpm > creator_participant.wpm:
            return battle.opponent
        else:
            return None  # Draw
    
    else:  # balanced
        # Score = WPM * accuracy / 100
        creator_score = creator_participant.wpm * (creator_participant.accuracy / 100)
        opponent_score = opponent_participant.wpm * (opponent_participant.accuracy / 100)
        
        if creator_score > opponent_score:
            return battle.creator
        elif opponent_score > creator_score:
            return battle.opponent
        else:
            return None  # Draw

