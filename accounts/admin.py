from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from django.urls import path, reverse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponseRedirect
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
            # Use getattr with default to avoid RelatedObjectDoesNotExist
            level_info = getattr(obj, 'level_info', None)
            if level_info:
                return format_html('<strong>Level {}</strong>', level_info.level)
            return '-'
        except Exception:
            return '-'
    user_level.short_description = 'Level'
    user_level.admin_order_field = 'level_info__level'
    
    def user_xp(self, obj):
        try:
            level_info = getattr(obj, 'level_info', None)
            if level_info:
                return format_html('{} XP', level_info.total_xp)
            return '-'
        except Exception:
            return '-'
    user_xp.short_description = 'XP'
    user_xp.admin_order_field = 'level_info__total_xp'
    
    def battle_stats(self, obj):
        try:
            # Use related_name 'battle_rating' from BattleRating model
            rating = getattr(obj, 'battle_rating', None)
            if rating:
                return format_html(
                    'W:{} L:{} D:{}<br><small>Rating: {}</small>',
                    rating.wins, rating.losses, rating.draws, rating.rating
                )
            return '-'
        except Exception:
            return '-'
    battle_stats.short_description = 'Battle'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Optimize queries by prefetching related objects (use correct related_name)
        return qs.select_related('level_info', 'battle_rating').prefetch_related('earned_badges')


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
                rate_str = f'{rate:.1f}'
                return format_html(
                    '<span style="color: {};"><strong>{}%</strong></span><br>'
                    '<small>{}/{} foydalanuvchi</small>',
                    color, rate_str, completed, total_users
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
    actions = ['mark_as_read', 'mark_as_unread', 'send_to_all_users', 'send_to_selected_users']
    
    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('user', 'notification_type', 'title', 'message', 'icon', 'link')
        }),
        ('Holat', {
            'fields': ('is_read', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
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
    
    @admin.action(description='Send notification to all users')
    def send_to_all_users(self, request, queryset):
        """Send notification to all users based on selected notification template"""
        if queryset.count() != 1:
            self.message_user(request, 'Iltimos, faqat bitta xabarni tanlang.', level='error')
            return
        
        template = queryset.first()
        from django.contrib.auth.models import User
        users = User.objects.filter(is_active=True)
        count = 0
        
        for user in users:
            Notification.objects.create(
                user=user,
                notification_type=template.notification_type,
                title=template.title,
                message=template.message,
                icon=template.icon,
                link=template.link,
                is_read=False
            )
            count += 1
        
        self.message_user(request, f'{count} foydalanuvchiga xabar yuborildi.')
    
    @admin.action(description='Send notification to selected users')
    def send_to_selected_users(self, request, queryset):
        """Send notification to users from selected notifications"""
        if queryset.count() != 1:
            self.message_user(request, 'Iltimos, faqat bitta xabarni tanlang.', level='error')
            return
        
        template = queryset.first()
        # Get unique users from selected notifications
        users = User.objects.filter(notifications__in=queryset).distinct()
        count = 0
        
        for user in users:
            Notification.objects.create(
                user=user,
                notification_type=template.notification_type,
                title=template.title,
                message=template.message,
                icon=template.icon,
                link=template.link,
                is_read=False
            )
            count += 1
        
        self.message_user(request, f'{count} foydalanuvchiga xabar yuborildi.')
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('send-notification/', self.admin_site.admin_view(self.send_notification_view), name='accounts_notification_send'),
        ]
        return custom_urls + urls
    
    def send_notification_view(self, request):
        """Custom view for sending notifications to users"""
        if request.method == 'POST':
            notification_type = request.POST.get('notification_type')
            title = request.POST.get('title')
            message = request.POST.get('message')
            icon = request.POST.get('icon', '🔔')
            link = request.POST.get('link', '')
            user_ids = request.POST.getlist('users')
            send_to_all = request.POST.get('send_to_all') == 'on'
            
            if not title or not message:
                messages.error(request, 'Sarlavha va xabar matni to\'ldirilishi shart.')
                return redirect('admin:accounts_notification_changelist')
            
            count = 0
            if send_to_all:
                users = User.objects.filter(is_active=True)
            else:
                if not user_ids:
                    messages.error(request, 'Kamida bitta foydalanuvchi tanlanishi kerak.')
                    return redirect('admin:accounts_notification_changelist')
                users = User.objects.filter(id__in=user_ids, is_active=True)
            
            for user in users:
                Notification.objects.create(
                    user=user,
                    notification_type=notification_type,
                    title=title,
                    message=message,
                    icon=icon,
                    link=link,
                    is_read=False
                )
                count += 1
            
            messages.success(request, f'{count} foydalanuvchiga xabar yuborildi.')
            return redirect('admin:accounts_notification_changelist')
        
        # GET request - show form
        users = User.objects.filter(is_active=True).order_by('username')
        context = {
            'title': 'Xabar yuborish',
            'users': users,
            'notification_types': Notification.NOTIFICATION_TYPE_CHOICES,
            'opts': self.model._meta,
            'has_view_permission': self.has_view_permission(request),
            'site_header': admin.site.site_header,
            'site_title': admin.site.site_title,
        }
        return render(request, 'admin/accounts/notification/send_notification.html', context)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user')


admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(UserProfile)
admin.site.register(UserLevel)
