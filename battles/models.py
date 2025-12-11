from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from typing_practice.models import Text, CodeSnippet


class Battle(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Kutilmoqda'),
        ('active', 'Faol'),
        ('finished', 'Tugallangan'),
        ('cancelled', 'Bekor qilingan'),
    ]
    
    MODE_CHOICES = [
        ('text', 'Matn'),
        ('code', 'Kod'),
    ]
    
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_battles')
    opponent = models.ForeignKey(User, on_delete=models.CASCADE, related_name='joined_battles', null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    mode = models.CharField(max_length=10, choices=MODE_CHOICES, default='text')
    text = models.ForeignKey(Text, on_delete=models.CASCADE, null=True, blank=True)
    code_snippet = models.ForeignKey(CodeSnippet, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    winner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='won_battles')
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['creator', 'status']),
            models.Index(fields=['opponent', 'status']),
        ]
    
    def __str__(self):
        return f"{self.creator.username} vs {self.opponent.username if self.opponent else 'Kutilmoqda'}"
    
    def start(self):
        """Start the battle"""
        if self.status == 'pending' and self.opponent:
            self.status = 'active'
            self.started_at = timezone.now()
            self.save()
    
    def finish(self):
        """Finish the battle"""
        if self.status == 'active':
            self.status = 'finished'
            self.finished_at = timezone.now()
            self.save()


class BattleParticipant(models.Model):
    battle = models.ForeignKey(Battle, on_delete=models.CASCADE, related_name='participants')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    wpm = models.FloatField(null=True, blank=True)
    accuracy = models.FloatField(null=True, blank=True)
    mistakes = models.IntegerField(default=0)
    finished_at = models.DateTimeField(null=True, blank=True)
    is_finished = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['battle', 'user']
        ordering = ['-wpm']
    
    def __str__(self):
        return f"{self.user.username} - {self.battle}"
