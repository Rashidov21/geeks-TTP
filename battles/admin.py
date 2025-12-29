from django.contrib import admin
from django.utils import timezone
from django.db.models import Avg, Count, Q
from django.utils.html import format_html
from .models import Battle, BattleParticipant, BattleRating, BattleInvitation
from datetime import timedelta


@admin.action(description='Mark selected battles as finished')
def mark_finished(modeladmin, request, queryset):
    queryset.update(status='finished', finished_at=timezone.now())


@admin.action(description='Delete battles older than 14 days')
def delete_old_battles(modeladmin, request, queryset):
    cutoff = timezone.now() - timedelta(days=14)
    old_battles = queryset.filter(created_at__lt=cutoff)
    count = old_battles.count()
    old_battles.delete()
    modeladmin.message_user(request, f'{count} eski battle o\'chirildi.')


@admin.register(Battle)
class BattleAdmin(admin.ModelAdmin):
    list_display = ['id', 'creator', 'opponent', 'status', 'mode', 'battle_type', 'winner', 'is_auto_match', 'created_at', 'battle_stats']
    list_filter = ['status', 'mode', 'battle_type', 'is_auto_match', ('created_at', admin.DateFieldListFilter)]
    search_fields = ['creator__username', 'opponent__username', 'id']
    readonly_fields = ['created_at', 'started_at', 'finished_at']
    actions = [mark_finished, delete_old_battles]
    date_hierarchy = 'created_at'
    
    def battle_stats(self, obj):
        participants = BattleParticipant.objects.filter(battle=obj)
        if participants.exists():
            avg_wpm = participants.aggregate(Avg('wpm'))['wpm__avg'] or 0
            avg_accuracy = participants.aggregate(Avg('accuracy'))['accuracy__avg'] or 0
            wpm_str = f'{avg_wpm:.1f}'
            accuracy_str = f'{avg_accuracy:.1f}'
            return format_html(
                '<span style="color: #3b82f6;">WPM: {}</span><br>'
                '<span style="color: #22c55e;">Aniqlik: {}%</span>',
                wpm_str, accuracy_str
            )
        return '-'
    battle_stats.short_description = 'Statistika'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('creator', 'opponent', 'winner')


@admin.register(BattleParticipant)
class BattleParticipantAdmin(admin.ModelAdmin):
    list_display = ['battle', 'user', 'wpm', 'accuracy', 'progress_percent', 'is_finished', 'mistakes']
    list_filter = ['is_finished', 'battle__status', 'battle__mode', 'battle__battle_type']
    search_fields = ['user__username', 'battle__id']
    readonly_fields = ['battle', 'user', 'wpm', 'accuracy', 'mistakes', 'progress_percent', 'is_finished']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('battle', 'user')


@admin.register(BattleRating)
class BattleRatingAdmin(admin.ModelAdmin):
    list_display = ['user', 'rating', 'wins', 'losses', 'draws', 'win_streak', 'total_battles', 'win_rate', 'last_updated']
    list_filter = [('last_updated', admin.DateFieldListFilter)]
    search_fields = ['user__username']
    readonly_fields = ['last_updated', 'rating', 'wins', 'losses', 'draws', 'win_streak', 'total_battles']
    ordering = ['-rating']
    
    def win_rate(self, obj):
        if obj.total_battles > 0:
            rate = (obj.wins / obj.total_battles) * 100
            color = '#22c55e' if rate >= 50 else '#ef4444' if rate < 30 else '#f59e0b'
            rate_str = f'{rate:.1f}'
            return format_html('<span style="color: {};">{}%</span>', color, rate_str)
        return '-'
    win_rate.short_description = 'G\'alaba %'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user')


@admin.register(BattleInvitation)
class BattleInvitationAdmin(admin.ModelAdmin):
    list_display = ['from_user', 'to_user', 'status', 'battle_mode', 'battle_type', 'created_at', 'expires_at']
    list_filter = ['status', 'battle_mode', 'battle_type', 'created_at']
    search_fields = ['from_user__username', 'to_user__username']
    readonly_fields = ['created_at', 'responded_at']
