from django.contrib import admin
from .models import Text, CodeSnippet, UserResult


@admin.register(Text)
class TextAdmin(admin.ModelAdmin):
    list_display = ['title', 'difficulty', 'created_at']
    list_filter = ['difficulty', 'created_at']
    search_fields = ['title', 'body']


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
