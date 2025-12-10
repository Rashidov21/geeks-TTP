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
    max_attempts_per_stage = models.IntegerField(default=3, help_text="Har bir bosqich uchun maksimal urinishlar soni")
    enable_certificates = models.BooleanField(default=False, help_text="Musobaqa tugatilganda sertifikatlar beriladimi?")
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
        indexes = [
            models.Index(fields=['competition', 'stage_number']),
        ]
    
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
        indexes = [
            models.Index(fields=['competition', '-result_wpm']),
            models.Index(fields=['user', 'competition']),
            models.Index(fields=['is_finished', '-result_wpm']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.competition.name}"
    
    def calculate_average_results(self):
        """Calculate and update average results from all stages"""
        from django.db.models import Avg
        stage_results = self.stage_results.filter(is_finished=True)
        if stage_results.exists():
            self.result_wpm = stage_results.aggregate(avg=Avg('wpm'))['avg']
            self.accuracy = stage_results.aggregate(avg=Avg('accuracy'))['avg']
            self.mistakes = sum(sr.mistakes for sr in stage_results)
            self.save()


class CompetitionParticipantStage(models.Model):
    participant = models.ForeignKey(CompetitionParticipant, on_delete=models.CASCADE, related_name='stage_results')
    stage = models.ForeignKey(CompetitionStage, on_delete=models.CASCADE)
    wpm = models.FloatField(null=True, blank=True)
    accuracy = models.FloatField(null=True, blank=True)
    mistakes = models.IntegerField(default=0)
    attempts = models.IntegerField(default=0, help_text="Bu bosqich uchun urinishlar soni")
    finished_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    is_finished = models.BooleanField(default=False)

    class Meta:
        unique_together = ['participant', 'stage']
        ordering = ['stage__stage_number']
        indexes = [
            models.Index(fields=['participant', 'stage']),
            models.Index(fields=['is_finished', '-wpm']),
        ]

    def __str__(self):
        return f"{self.participant.user.username} - {self.stage.competition.name} - Stage {self.stage.stage_number}"
    
    def can_attempt(self):
        """Check if participant can make another attempt"""
        return self.attempts < self.stage.competition.max_attempts_per_stage


class Certificate(models.Model):
    """Certificate configuration for competitions"""
    competition = models.OneToOneField(Competition, on_delete=models.CASCADE, related_name='certificate')
    logo = models.ImageField(upload_to='certificates/logos/', null=True, blank=True, help_text="Sertifikat logosi (yuqorida ko'rinadi)")
    organization_name = models.CharField(max_length=200, default="GEEKS ANDIJAN", help_text="Tashkilot nomi (sarlavha)")
    certificate_subtitle = models.CharField(max_length=200, default="Typing Competition Certificate", help_text="Sertifikat pastki sarlavhasi")
    additional_names = models.TextField(blank=True, help_text="Qo'shimcha nomlar (har bir qator alohida, footer'da ko'rinadi)")
    signature_name = models.CharField(max_length=200, blank=True, help_text="Imzo nomi (masalan: Geeks Andijan)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Certificate for {self.competition.name}"
    
    def get_additional_names_list(self):
        """Return additional names as a list"""
        if not self.additional_names:
            return []
        return [name.strip() for name in self.additional_names.split('\n') if name.strip()]
