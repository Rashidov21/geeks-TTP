from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import (
    UserProfile, Badge, UserBadge, UserLevel, 
    DailyChallenge, ChallengeCompletion, Notification
)


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'


class UserLevelInline(admin.StackedInline):
    model = UserLevel
    can_delete = False
    verbose_name_plural = 'Level Info'


class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline, UserLevelInline)


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ['name', 'badge_type', 'xp_reward', 'is_active']
    list_filter = ['badge_type', 'is_active']
    search_fields = ['name', 'description']


@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display = ['user', 'badge', 'earned_at', 'progress']
    list_filter = ['badge', 'earned_at']
    search_fields = ['user__username', 'badge__name']


@admin.register(DailyChallenge)
class DailyChallengeAdmin(admin.ModelAdmin):
    list_display = ['date', 'title', 'challenge_type', 'reward_xp', 'is_active']
    list_filter = ['challenge_type', 'is_active', 'date']
    search_fields = ['title', 'description']


@admin.register(ChallengeCompletion)
class ChallengeCompletionAdmin(admin.ModelAdmin):
    list_display = ['user', 'challenge', 'completed_at', 'xp_earned']
    list_filter = ['challenge', 'completed_at']
    search_fields = ['user__username', 'challenge__title']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'notification_type', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['user__username', 'title', 'message']
    readonly_fields = ['created_at']


admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(UserProfile)
admin.site.register(UserLevel)
