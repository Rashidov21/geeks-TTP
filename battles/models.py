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
    
    BATTLE_TYPE_CHOICES = [
        ('speed', 'Tezlik'),
        ('accuracy', 'Aniqlik'),
        ('endurance', 'Chidamlilik'),
        ('balanced', 'Muvozanatli'),
    ]
    
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_battles')
    opponent = models.ForeignKey(User, on_delete=models.CASCADE, related_name='joined_battles', null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    mode = models.CharField(max_length=10, choices=MODE_CHOICES, default='text')
    battle_type = models.CharField(max_length=20, choices=BATTLE_TYPE_CHOICES, default='balanced', help_text="Jang turi")
    text = models.ForeignKey(Text, on_delete=models.CASCADE, null=True, blank=True)
    code_snippet = models.ForeignKey(CodeSnippet, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    winner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='won_battles')
    
    # Time limit and countdown
    time_limit_seconds = models.IntegerField(default=300, help_text="Vaqt limiti (soniya)")
    countdown_seconds = models.IntegerField(default=3, help_text="Countdown (soniya)")
    
    # Rematch
    rematch_of = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='rematches', help_text="Qaysi jangning rematch'i")
    
    # Auto-matchmaking
    is_auto_match = models.BooleanField(default=False, help_text="Avtomatik matchmaking orqali yaratilgan")
    
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
    progress_percent = models.FloatField(default=0, help_text="Jarayon foizi (0-100)")
    
    class Meta:
        unique_together = ['battle', 'user']
        ordering = ['-wpm']
    
    def __str__(self):
        return f"{self.user.username} - {self.battle}"


class BattleRating(models.Model):
    """Battle rating/ELO system"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='battle_rating')
    rating = models.IntegerField(default=1000, help_text="ELO rating")
    wins = models.IntegerField(default=0)
    losses = models.IntegerField(default=0)
    draws = models.IntegerField(default=0)
    win_streak = models.IntegerField(default=0)
    best_win_streak = models.IntegerField(default=0)
    total_battles = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-rating']
        indexes = [
            models.Index(fields=['-rating']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - Rating: {self.rating}"
    
    def get_win_rate(self):
        """Calculate win rate percentage"""
        if self.total_battles == 0:
            return 0
        return round((self.wins / self.total_battles) * 100, 1)


class BattleInvitation(models.Model):
    """Battle invitations between users"""
    STATUS_CHOICES = [
        ('pending', 'Kutilmoqda'),
        ('accepted', 'Qabul qilindi'),
        ('rejected', 'Rad etildi'),
        ('expired', 'Muddati tugagan'),
    ]
    
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_battle_invitations')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_battle_invitations')
    battle = models.ForeignKey(Battle, on_delete=models.CASCADE, related_name='invitations', null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    battle_mode = models.CharField(max_length=10, choices=Battle.MODE_CHOICES, default='text')
    battle_type = models.CharField(max_length=20, choices=Battle.BATTLE_TYPE_CHOICES, default='balanced')
    time_limit_seconds = models.IntegerField(default=300)
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(help_text="Taklifning amal qilish muddati")
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['to_user', 'status']),
            models.Index(fields=['from_user', 'status']),
        ]
    
    def __str__(self):
        return f"{self.from_user.username} -> {self.to_user.username} ({self.status})"
    
    def is_expired(self):
        """Check if invitation is expired"""
        return timezone.now() > self.expires_at
