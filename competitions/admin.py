from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Avg, Count, Max
from .models import Competition, CompetitionParticipant, CompetitionStage, CompetitionParticipantStage, Certificate


class CompetitionStageInline(admin.TabularInline):
    model = CompetitionStage
    extra = 0


class CompetitionParticipantInline(admin.TabularInline):
    model = CompetitionParticipant
    extra = 0
    readonly_fields = ['finished_at', 'started_at']


@admin.register(Competition)
class CompetitionAdmin(admin.ModelAdmin):
    list_display = ['name', 'mode', 'difficulty', 'status', 'participant_count', 'avg_wpm', 'enable_certificates', 'start_time', 'created_by', 'created_at']
    list_filter = ['mode', 'difficulty', 'status', 'enable_certificates', ('start_time', admin.DateFieldListFilter), ('created_at', admin.DateFieldListFilter)]
    search_fields = ['name', 'access_code', 'created_by__username']
    inlines = [CompetitionStageInline, CompetitionParticipantInline]
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at', 'competition_stats']
    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('name', 'mode', 'difficulty', 'status', 'created_by', 'access_code', 'is_public')
        }),
        ('Vaqt', {
            'fields': ('start_time',)
        }),
        ('Sozlamalar', {
            'fields': ('enable_certificates', 'max_attempts_per_stage')
        }),
        ('Statistika', {
            'fields': ('competition_stats',),
            'classes': ('collapse',)
        }),
    )
    
    def participant_count(self, obj):
        count = obj.participants.count()
        finished = CompetitionParticipant.objects.filter(competition=obj, is_finished=True).count()
        return format_html(
            '<strong>{}</strong> / {} tugatgan',
            finished, count
        )
    participant_count.short_description = 'Ishtirokchilar'
    
    def avg_wpm(self, obj):
        avg = CompetitionParticipant.objects.filter(
            competition=obj, 
            result_wpm__isnull=False
        ).aggregate(Avg('result_wpm'))['result_wpm__avg']
        if avg:
            avg_str = f'{avg:.1f}'
            return format_html('<strong>{}</strong>', avg_str)
        return '-'
    avg_wpm.short_description = 'O\'rtacha WPM'
    
    def competition_stats(self, obj):
        if obj.pk:
            participants = CompetitionParticipant.objects.filter(competition=obj)
            total = participants.count()
            finished = participants.filter(is_finished=True).count()
            avg_wpm = participants.filter(result_wpm__isnull=False).aggregate(Avg('result_wpm'))['result_wpm__avg'] or 0
            avg_accuracy = participants.filter(accuracy__isnull=False).aggregate(Avg('accuracy'))['accuracy__avg'] or 0
            max_wpm = participants.filter(result_wpm__isnull=False).aggregate(Max('result_wpm'))['result_wpm__max'] or 0
            
            avg_wpm_str = f'{avg_wpm:.1f}'
            avg_accuracy_str = f'{avg_accuracy:.1f}'
            max_wpm_str = f'{max_wpm:.1f}'
            return format_html(
                '<strong>Jami ishtirokchilar:</strong> {}<br>'
                '<strong>Tugatgan:</strong> {}<br>'
                '<strong>O\'rtacha WPM:</strong> {}<br>'
                '<strong>O\'rtacha aniqlik:</strong> {}%<br>'
                '<strong>Eng yuqori WPM:</strong> {}',
                total, finished, avg_wpm_str, avg_accuracy_str, max_wpm_str
            )
        return 'Saqlangandan keyin ko\'rsatiladi'
    competition_stats.short_description = 'Statistika'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('created_by').prefetch_related('participants')


@admin.register(CompetitionParticipant)
class CompetitionParticipantAdmin(admin.ModelAdmin):
    list_display = ['user', 'competition', 'result_wpm', 'accuracy', 'current_stage', 'is_finished', 'rank', 'finished_at']
    list_filter = ['is_finished', 'competition', 'competition__status', 'competition__mode']
    search_fields = ['user__username', 'competition__name']
    readonly_fields = ['started_at', 'finished_at', 'result_wpm', 'accuracy', 'current_stage']
    date_hierarchy = 'started_at'
    
    def rank(self, obj):
        try:
            if obj.is_finished and obj.result_wpm is not None:
                # Calculate rank based on WPM
                better_count = CompetitionParticipant.objects.filter(
                    competition=obj.competition,
                    is_finished=True,
                    result_wpm__gt=obj.result_wpm
                ).count()
                rank = better_count + 1
                medal = '🥇' if rank == 1 else '🥈' if rank == 2 else '🥉' if rank == 3 else ''
                return format_html('{} {}', medal, rank)
            return '-'
        except Exception:
            return '-'
    rank.short_description = 'O\'rin'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user', 'competition')


@admin.register(CompetitionStage)
class CompetitionStageAdmin(admin.ModelAdmin):
    list_display = ['competition', 'stage_number', 'text', 'code_snippet']
    list_filter = ['competition', 'stage_number']


@admin.register(CompetitionParticipantStage)
class CompetitionParticipantStageAdmin(admin.ModelAdmin):
    list_display = ['participant', 'stage', 'wpm', 'accuracy', 'attempts', 'is_finished']
    list_filter = ['is_finished', 'stage']
    readonly_fields = ['attempts']


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ['competition', 'has_logo', 'has_additional_names', 'created_at', 'updated_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['competition__name']
    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('competition',)
        }),
        ('Dizayn sozlamalari', {
            'fields': ('logo', 'organization_name', 'certificate_subtitle', 'signature_name', 'additional_names'),
            'description': 'Sertifikat dizaynini to\'ldiring. Logo va qo\'shimcha nomlar ixtiyoriy.'
        }),
    )
    readonly_fields = ['created_at', 'updated_at']
    
    def has_logo(self, obj):
        return bool(obj.logo)
    has_logo.short_description = "Logo"
    has_logo.boolean = True
    
    def has_additional_names(self, obj):
        return bool(obj.additional_names)
    has_additional_names.short_description = "Qo'shimcha nomlar"
    has_additional_names.boolean = True
