from django.db import models
from django.contrib.auth.models import User
from typing_practice.models import Text, CodeSnippet


class Competition(models.Model):
    MODE_CHOICES = [
        ('text', 'Text'),
        ('code', 'Code'),
        ('1v1', '1v1 Duel'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('finished', 'Finished'),
    ]
    
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('hard', 'Hard'),
    ]
    
    name = models.CharField(max_length=200)
    mode = models.CharField(max_length=10, choices=MODE_CHOICES)
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='easy')
    text = models.ForeignKey(Text, on_delete=models.CASCADE, null=True, blank=True)
    code_snippet = models.ForeignKey(CodeSnippet, on_delete=models.CASCADE, null=True, blank=True)
    start_time = models.DateTimeField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_competitions')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    participants = models.ManyToManyField(User, through='CompetitionParticipant', related_name='competitions')
    access_code = models.CharField(max_length=20, unique=True, null=True, blank=True)
    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.mode})"


class CompetitionStage(models.Model):
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, related_name='stages')
    stage_number = models.IntegerField()  # 1, 2, or 3
    text = models.ForeignKey(Text, on_delete=models.CASCADE, null=True, blank=True)
    code_snippet = models.ForeignKey(CodeSnippet, on_delete=models.CASCADE, null=True, blank=True)
    
    class Meta:
        unique_together = ['competition', 'stage_number']
        ordering = ['stage_number']
    
    def __str__(self):
        return f"{self.competition.name} - Stage {self.stage_number}"


class CompetitionParticipant(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE)
    result_wpm = models.FloatField(null=True, blank=True)  # Average WPM across all stages
    accuracy = models.FloatField(null=True, blank=True)  # Average accuracy
    mistakes = models.IntegerField(default=0)  # Total mistakes
    finished_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    is_finished = models.BooleanField(default=False)
    current_stage = models.IntegerField(default=1)

    class Meta:
        unique_together = ['user', 'competition']
        ordering = ['-result_wpm']

    def __str__(self):
        return f"{self.user.username} - {self.competition.name}"


class CompetitionParticipantStage(models.Model):
    participant = models.ForeignKey(CompetitionParticipant, on_delete=models.CASCADE, related_name='stage_results')
    stage = models.ForeignKey(CompetitionStage, on_delete=models.CASCADE)
    wpm = models.FloatField(null=True, blank=True)
    accuracy = models.FloatField(null=True, blank=True)
    mistakes = models.IntegerField(default=0)
    finished_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    is_finished = models.BooleanField(default=False)

    class Meta:
        unique_together = ['participant', 'stage']
        ordering = ['stage__stage_number']

    def __str__(self):
        return f"{self.participant.user.username} - {self.stage.competition.name} - Stage {self.stage.stage_number}"
