from django.contrib import admin
from .models import Text, CodeSnippet, UserResult


@admin.register(Text)
class TextAdmin(admin.ModelAdmin):
    list_display = ['title', 'difficulty', 'word_count', 'created_at']
    list_filter = ['difficulty', 'word_count', 'created_at']
    search_fields = ['title', 'body']
    fields = ['title', 'difficulty', 'word_count', 'body']
    readonly_fields = ['created_at']
    
    def save_model(self, request, obj, form, change):
        # Validate word count matches actual body word count
        actual_word_count = len(obj.body.split())
        if abs(actual_word_count - obj.word_count) > 2:  # Allow 2 words difference
            from django.contrib import messages
            messages.warning(request, f'Eslatma: Matndagi haqiqiy so\'zlar soni ({actual_word_count}) belgilangan so\'zlar sonidan ({obj.word_count}) farq qiladi.')
        super().save_model(request, obj, form, change)


@admin.register(CodeSnippet)
class CodeSnippetAdmin(admin.ModelAdmin):
    list_display = ['title', 'language', 'difficulty', 'created_at']
    list_filter = ['language', 'difficulty', 'created_at']
    search_fields = ['title', 'code_body']


@admin.register(UserResult)
class UserResultAdmin(admin.ModelAdmin):
    list_display = ['user', 'session_type', 'wpm', 'accuracy', 'date', 'time']
    list_filter = ['session_type', 'date', 'time']
    search_fields = ['user__username']
    readonly_fields = ['time', 'date']
