from django.contrib import admin
from .models import Competition, CompetitionParticipant, CompetitionStage, CompetitionParticipantStage


class CompetitionStageInline(admin.TabularInline):
    model = CompetitionStage
    extra = 0


class CompetitionParticipantInline(admin.TabularInline):
    model = CompetitionParticipant
    extra = 0
    readonly_fields = ['finished_at', 'started_at']


@admin.register(Competition)
class CompetitionAdmin(admin.ModelAdmin):
    list_display = ['name', 'mode', 'difficulty', 'status', 'start_time', 'created_by', 'created_at']
    list_filter = ['mode', 'difficulty', 'status', 'start_time', 'created_at']
    search_fields = ['name', 'access_code']
    inlines = [CompetitionStageInline, CompetitionParticipantInline]


@admin.register(CompetitionParticipant)
class CompetitionParticipantAdmin(admin.ModelAdmin):
    list_display = ['user', 'competition', 'result_wpm', 'accuracy', 'current_stage', 'is_finished', 'finished_at']
    list_filter = ['is_finished', 'competition']
    search_fields = ['user__username', 'competition__name']


@admin.register(CompetitionStage)
class CompetitionStageAdmin(admin.ModelAdmin):
    list_display = ['competition', 'stage_number', 'text', 'code_snippet']
    list_filter = ['competition', 'stage_number']


@admin.register(CompetitionParticipantStage)
class CompetitionParticipantStageAdmin(admin.ModelAdmin):
    list_display = ['participant', 'stage', 'wpm', 'accuracy', 'is_finished']
    list_filter = ['is_finished', 'stage']
