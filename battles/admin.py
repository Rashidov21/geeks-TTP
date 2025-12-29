from django.contrib import admin
from .models import Battle, BattleParticipant, BattleRating, BattleInvitation


@admin.register(Battle)
class BattleAdmin(admin.ModelAdmin):
    list_display = ['id', 'creator', 'opponent', 'status', 'mode', 'battle_type', 'winner', 'is_auto_match', 'created_at']
    list_filter = ['status', 'mode', 'battle_type', 'is_auto_match', 'created_at']
    search_fields = ['creator__username', 'opponent__username']
    readonly_fields = ['created_at', 'started_at', 'finished_at']


@admin.register(BattleParticipant)
class BattleParticipantAdmin(admin.ModelAdmin):
    list_display = ['battle', 'user', 'wpm', 'accuracy', 'progress_percent', 'is_finished']
    list_filter = ['is_finished', 'battle__status']
    search_fields = ['user__username', 'battle__id']


@admin.register(BattleRating)
class BattleRatingAdmin(admin.ModelAdmin):
    list_display = ['user', 'rating', 'wins', 'losses', 'draws', 'win_streak', 'total_battles', 'last_updated']
    list_filter = ['last_updated']
    search_fields = ['user__username']
    readonly_fields = ['last_updated']
    ordering = ['-rating']


@admin.register(BattleInvitation)
class BattleInvitationAdmin(admin.ModelAdmin):
    list_display = ['from_user', 'to_user', 'status', 'battle_mode', 'battle_type', 'created_at', 'expires_at']
    list_filter = ['status', 'battle_mode', 'battle_type', 'created_at']
    search_fields = ['from_user__username', 'to_user__username']
    readonly_fields = ['created_at', 'responded_at']
