from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from .models import (
    UserProfile, Badge, UserBadge, UserLevel, 
    DailyChallenge, ChallengeCompletion, Notification
)
from battles.models import BattleRating


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'


class UserLevelInline(admin.StackedInline):
    model = UserLevel
    can_delete = False
    verbose_name_plural = 'Level Info'
    readonly_fields = ['current_xp', 'total_xp', 'level', 'updated_at']
    fields = ['level', 'current_xp', 'total_xp', 'updated_at']


class UserBadgeInline(admin.TabularInline):
    model = UserBadge
    extra = 0
    readonly_fields = ['badge', 'earned_at', 'progress']
    fields = ['badge', 'earned_at', 'progress']


class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline, UserLevelInline, UserBadgeInline)
    list_display = ['username', 'email', 'first_name', 'last_name', 'user_level', 'user_xp', 'battle_stats', 'is_staff', 'date_joined']
    list_filter = ['is_staff', 'is_superuser', 'is_active', 'date_joined']
    
    def user_level(self, obj):
        try:
            level_info = obj.level_info
            return format_html('<strong>Level {}</strong>', level_info.level)
        except:
            return '-'
    user_level.short_description = 'Level'
    
    def user_xp(self, obj):
        try:
            level_info = obj.level_info
            return format_html('{} XP', level_info.total_xp)
        except:
            return '-'
    user_xp.short_description = 'XP'
    
    def battle_stats(self, obj):
        try:
            rating = BattleRating.objects.get(user=obj)
            return format_html(
                'W:{} L:{} D:{}<br><small>Rating: {}</small>',
                rating.wins, rating.losses, rating.draws, rating.rating
            )
        except:
            return '-'
    battle_stats.short_description = 'Battle'


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ['icon', 'name', 'badge_type', 'xp_reward', 'earned_count', 'is_active']
    list_filter = ['badge_type', 'is_active']
    search_fields = ['name', 'description']
    readonly_fields = ['earned_count_display']
    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('name', 'description', 'icon', 'badge_type', 'is_active')
        }),
        ('Talablar', {
            'fields': ('requirement',),
            'description': 'JSON formatida talablar (masalan: {"wpm": 100, "sessions": 50})'
        }),
        ('Mukofot', {
            'fields': ('xp_reward',)
        }),
        ('Statistika', {
            'fields': ('earned_count_display',)
        }),
    )
    
    def earned_count(self, obj):
        count = UserBadge.objects.filter(badge=obj).count()
        return format_html('<strong>{}</strong>', count)
    earned_count.short_description = 'Olganlar soni'
    
    def earned_count_display(self, obj):
        if obj.pk:
            count = UserBadge.objects.filter(badge=obj).count()
            users = UserBadge.objects.filter(badge=obj).select_related('user')[:10]
            user_list = ', '.join([ub.user.username for ub in users])
            if count > 10:
                user_list += f' va yana {count - 10} ta foydalanuvchi'
            return format_html('<strong>Jami: {}</strong><br><small>{}</small>', count, user_list or 'Hali hech kim olmagan')
        return 'Saqlangandan keyin ko\'rsatiladi'
    earned_count_display.short_description = 'Olgan foydalanuvchilar'


@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display = ['user', 'badge_icon', 'badge', 'earned_at', 'progress']
    list_filter = ['badge', 'badge__badge_type', ('earned_at', admin.DateFieldListFilter)]
    search_fields = ['user__username', 'badge__name']
    readonly_fields = ['earned_at']
    date_hierarchy = 'earned_at'
    
    def badge_icon(self, obj):
        return format_html('<span style="font-size: 1.5em;">{}</span>', obj.badge.icon)
    badge_icon.short_description = 'Icon'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user', 'badge')


@admin.register(DailyChallenge)
class DailyChallengeAdmin(admin.ModelAdmin):
    list_display = ['date', 'title', 'challenge_type', 'reward_xp', 'completion_rate', 'is_active']
    list_filter = ['challenge_type', 'is_active', ('date', admin.DateFieldListFilter)]
    search_fields = ['title', 'description']
    date_hierarchy = 'date'
    
    def completion_rate(self, obj):
        if obj.pk:
            total_users = User.objects.count()
            completed = ChallengeCompletion.objects.filter(challenge=obj).count()
            if total_users > 0:
                rate = (completed / total_users) * 100
                color = '#22c55e' if rate >= 50 else '#ef4444' if rate < 20 else '#f59e0b'
                return format_html(
                    '<span style="color: {};"><strong>{:.1f}%</strong></span><br>'
                    '<small>{}/{} foydalanuvchi</small>',
                    color, rate, completed, total_users
                )
        return '-'
    completion_rate.short_description = 'Bajarilish %'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related('completions')


@admin.register(ChallengeCompletion)
class ChallengeCompletionAdmin(admin.ModelAdmin):
    list_display = ['user', 'challenge', 'completed_at', 'xp_earned']
    list_filter = ['challenge', 'completed_at']
    search_fields = ['user__username', 'challenge__title']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'icon', 'title', 'notification_type', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', ('created_at', admin.DateFieldListFilter)]
    search_fields = ['user__username', 'title', 'message']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    actions = ['mark_as_read', 'mark_as_unread', 'resend_notification']
    
    def icon(self, obj):
        return format_html('<span style="font-size: 1.2em;">{}</span>', obj.icon or '📢')
    icon.short_description = 'Icon'
    
    @admin.action(description='Mark selected notifications as read')
    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, f'{updated} xabar o\'qilgan deb belgilandi.')
    
    @admin.action(description='Mark selected notifications as unread')
    def mark_as_unread(self, request, queryset):
        updated = queryset.update(is_read=False)
        self.message_user(request, f'{updated} xabar o\'qilmagan deb belgilandi.')
    
    @admin.action(description='Resend selected notifications')
    def resend_notification(self, request, queryset):
        # This would trigger notification sending logic
        count = queryset.count()
        self.message_user(request, f'{count} xabar qayta yuborish funksiyasi keyingi versiyada qo\'shiladi.')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user')


admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(UserProfile)
admin.site.register(UserLevel)
