from django.contrib import admin
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
    list_display = ['name', 'mode', 'difficulty', 'status', 'enable_certificates', 'start_time', 'created_by', 'created_at']
    list_filter = ['mode', 'difficulty', 'status', 'enable_certificates', 'start_time', 'created_at']
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
