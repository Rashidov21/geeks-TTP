from django.contrib import admin
from .models import Battle, BattleParticipant


@admin.register(Battle)
class BattleAdmin(admin.ModelAdmin):
    list_display = ['id', 'creator', 'opponent', 'status', 'mode', 'winner', 'created_at']
    list_filter = ['status', 'mode', 'created_at']
    search_fields = ['creator__username', 'opponent__username']
    readonly_fields = ['created_at', 'started_at', 'finished_at']


@admin.register(BattleParticipant)
class BattleParticipantAdmin(admin.ModelAdmin):
    list_display = ['battle', 'user', 'wpm', 'accuracy', 'is_finished']
    list_filter = ['is_finished', 'battle__status']
    search_fields = ['user__username', 'battle__id']
