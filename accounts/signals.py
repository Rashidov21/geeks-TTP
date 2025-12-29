from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import UserProfile, UserLevel
from typing_practice.models import UserResult
from .gamification import update_streak, award_xp_for_practice, check_and_award_badges, check_daily_challenge


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)
        # Create UserLevel for new user
        UserLevel.objects.get_or_create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'userprofile'):
        instance.userprofile.save()
    else:
        UserProfile.objects.get_or_create(user=instance)


@receiver(post_save, sender=UserResult)
def handle_user_result(sender, instance, created, **kwargs):
    """Handle gamification when user completes a practice"""
    if created:
        # Update streak
        update_streak(instance.user)
        
        # Award XP
        award_xp_for_practice(instance.user, instance)
        
        # Check for badges
        check_and_award_badges(instance.user, instance)
        
        # Check daily challenge
        check_daily_challenge(instance.user, instance)

