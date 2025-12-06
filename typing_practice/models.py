from django.db import models
from django.contrib.auth.models import User


class Text(models.Model):
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('hard', 'Hard'),
    ]
    
    title = models.CharField(max_length=200)
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['difficulty']),
        ]

    def __str__(self):
        return f"{self.title} ({self.difficulty})"


class CodeSnippet(models.Model):
    LANGUAGE_CHOICES = [
        ('python', 'Python'),
        ('javascript', 'JavaScript'),
        ('cpp', 'C++'),
        ('java', 'Java'),
    ]
    
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]
    
    title = models.CharField(max_length=200)
    language = models.CharField(max_length=20, choices=LANGUAGE_CHOICES)
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES)
    code_body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['language', 'difficulty']),
        ]

    def __str__(self):
        return f"{self.title} ({self.language})"


class UserResult(models.Model):
    SESSION_TYPE_CHOICES = [
        ('text', 'Text'),
        ('code', 'Code'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.ForeignKey(Text, on_delete=models.CASCADE, null=True, blank=True)
    code_snippet = models.ForeignKey(CodeSnippet, on_delete=models.CASCADE, null=True, blank=True)
    wpm = models.FloatField()
    accuracy = models.FloatField()
    mistakes = models.IntegerField(default=0)
    mistakes_list = models.JSONField(default=list, blank=True)
    date = models.DateField(auto_now_add=True)
    time = models.DateTimeField(auto_now_add=True)
    session_type = models.CharField(max_length=10, choices=SESSION_TYPE_CHOICES)
    duration_seconds = models.IntegerField(default=0)

    class Meta:
        ordering = ['-time']
        indexes = [
            models.Index(fields=['user', '-time']),
            models.Index(fields=['session_type', '-time']),
            models.Index(fields=['-wpm']),
            models.Index(fields=['-time']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.wpm} WPM - {self.accuracy}%"
