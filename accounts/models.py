from django.contrib.auth.models import User
from django.db import models
from django.core.files.base import ContentFile
from io import BytesIO
import os
import logging

logger = logging.getLogger('typing_platform')

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logger.warning("PIL/Pillow is not installed. Image resizing will be disabled.")


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_manager = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to='profiles/', null=True, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    address = models.CharField(max_length=200, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    # Streak fields
    current_streak = models.IntegerField(default=0, help_text="Joriy ketma-ketlik (kun)")
    longest_streak = models.IntegerField(default=0, help_text="Eng uzun ketma-ketlik")
    last_practice_date = models.DateField(null=True, blank=True, help_text="Oxirgi mashq qilgan sana")
    total_practice_days = models.IntegerField(default=0, help_text="Jami mashq qilgan kunlar")

    def __str__(self):
        return f"{self.user.username} - {'Manager' if self.is_manager else 'User'}"
    
    def save(self, *args, **kwargs):
        # Check if image is being updated and PIL is available
        if self.image and PIL_AVAILABLE:
            # Check if this is a new image or image has changed
            image_changed = False
            old_image_path = None
            
            if self.pk:
                try:
                    old_profile = UserProfile.objects.get(pk=self.pk)
                    if old_profile.image:
                        old_image_path = old_profile.image.path
                        # Check if image has changed
                        if old_profile.image.name != self.image.name:
                            image_changed = True
                    else:
                        # No old image, so this is new
                        image_changed = True
                except UserProfile.DoesNotExist:
                    image_changed = True
            else:
                # New profile, image is new
                image_changed = True
            
            # Only process if image is new or changed
            if image_changed:
                try:
                    # Open the image
                    img = Image.open(self.image)
                    
                    # Convert RGBA to RGB if necessary
                    if img.mode in ('RGBA', 'LA', 'P'):
                        background = Image.new('RGB', img.size, (255, 255, 255))
                        if img.mode == 'P':
                            img = img.convert('RGBA')
                        if img.mode == 'RGBA':
                            background.paste(img, mask=img.split()[-1])
                        else:
                            background.paste(img)
                        img = background
                    elif img.mode != 'RGB':
                        img = img.convert('RGB')
                    
                    # Resize image to 400x400 (maintaining aspect ratio)
                    max_size = (400, 400)
                    img.thumbnail(max_size, Image.Resampling.LANCZOS)
                    
                    # Save to BytesIO with compression
                    img_io = BytesIO()
                    img.save(img_io, format='JPEG', quality=85, optimize=True)
                    img_io.seek(0)
                    
                    # Generate filename
                    filename = self.image.name.split('/')[-1]
                    if not filename.endswith('.jpg') and not filename.endswith('.jpeg'):
                        filename = filename.rsplit('.', 1)[0] + '.jpg'
                    
                    # Save the compressed image
                    self.image.save(
                        filename,
                        ContentFile(img_io.read()),
                        save=False
                    )
                    
                    # Delete old image after successful save
                    if old_image_path and os.path.isfile(old_image_path):
                        try:
                            os.remove(old_image_path)
                        except Exception as e:
                            logger.warning(f"Could not delete old image: {e}")
                            
                except Exception as e:
                    # If image processing fails, log and save normally
                    logger.error(f"Error processing profile image: {e}", exc_info=True)
        
        super().save(*args, **kwargs)


class Badge(models.Model):
    """Badge/Achievement model"""
    BADGE_TYPE_CHOICES = [
        ('speed', 'Tezlik'),
        ('accuracy', 'Aniqlik'),
        ('streak', 'Ketma-ketlik'),
        ('milestone', 'Yutuq'),
        ('competition', 'Musobaqa'),
        ('consistency', 'Izchillik'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    icon = models.CharField(max_length=50, default='🏆', help_text="Emoji yoki icon")
    badge_type = models.CharField(max_length=20, choices=BADGE_TYPE_CHOICES)
    requirement = models.JSONField(default=dict, help_text="Talablar (masalan: {'wpm': 100, 'sessions': 50})")
    xp_reward = models.IntegerField(default=50, help_text="XP mukofoti")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['badge_type', 'name']
        indexes = [
            models.Index(fields=['badge_type', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.icon} {self.name}"


class UserBadge(models.Model):
    """User's earned badges"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='earned_badges')
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE, related_name='user_badges')
    earned_at = models.DateTimeField(auto_now_add=True)
    progress = models.IntegerField(default=100, help_text="Progress foizi (0-100)")
    
    class Meta:
        unique_together = ['user', 'badge']
        ordering = ['-earned_at']
        indexes = [
            models.Index(fields=['user', '-earned_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.badge.name}"


class UserLevel(models.Model):
    """User XP and Level system"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='level_info')
    current_xp = models.IntegerField(default=0)
    total_xp = models.IntegerField(default=0)
    level = models.IntegerField(default=1)
    updated_at = models.DateTimeField(auto_now=True)
    
    def calculate_level(self):
        """Calculate level from total XP"""
        # Level formula: Level N requires sum(100 * 1.5^(i-1)) for i=1 to N-1
        xp = self.total_xp
        level = 1
        required_xp = 0
        
        while True:
            level_xp = int(100 * (1.5 ** (level - 1)))
            if required_xp + level_xp > xp:
                break
            required_xp += level_xp
            level += 1
        
        self.level = level
        self.current_xp = xp - required_xp
        return level
    
    def get_xp_for_next_level(self):
        """Get XP required for next level"""
        return int(100 * (1.5 ** (self.level - 1)))
    
    def get_progress_percentage(self):
        """Get progress percentage to next level"""
        next_level_xp = self.get_xp_for_next_level()
        if next_level_xp == 0:
            return 100
        return int((self.current_xp / next_level_xp) * 100)
    
    def add_xp(self, amount):
        """Add XP and update level"""
        self.total_xp += amount
        old_level = self.level
        self.calculate_level()
        level_up = self.level > old_level
        self.save()
        return level_up, self.level
    
    def __str__(self):
        return f"{self.user.username} - Level {self.level} ({self.total_xp} XP)"


class DailyChallenge(models.Model):
    """Daily challenge for users"""
    CHALLENGE_TYPE_CHOICES = [
        ('speed', 'Tezlik'),
        ('accuracy', 'Aniqlik'),
        ('code', 'Kod'),
        ('text', 'Matn'),
        ('consistency', 'Izchillik'),
    ]
    
    date = models.DateField(unique=True)
    challenge_type = models.CharField(max_length=20, choices=CHALLENGE_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    description = models.TextField()
    target_wpm = models.IntegerField(null=True, blank=True)
    target_accuracy = models.FloatField(null=True, blank=True)
    target_sessions = models.IntegerField(null=True, blank=True, default=1)
    reward_xp = models.IntegerField(default=50)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date']
        indexes = [
            models.Index(fields=['date', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.date} - {self.title}"


class ChallengeCompletion(models.Model):
    """User's challenge completions"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='challenge_completions')
    challenge = models.ForeignKey(DailyChallenge, on_delete=models.CASCADE, related_name='completions')
    completed_at = models.DateTimeField(auto_now_add=True)
    result_wpm = models.FloatField(null=True, blank=True)
    result_accuracy = models.FloatField(null=True, blank=True)
    xp_earned = models.IntegerField(default=0)
    
    class Meta:
        unique_together = ['user', 'challenge']
        ordering = ['-completed_at']
        indexes = [
            models.Index(fields=['user', '-completed_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.challenge.title}"


class Notification(models.Model):
    """User notifications"""
    NOTIFICATION_TYPE_CHOICES = [
        ('badge', 'Badge'),
        ('level_up', 'Level Up'),
        ('challenge', 'Challenge'),
        ('competition', 'Musobaqa'),
        ('battle', 'Battle'),
        ('streak', 'Streak'),
        ('achievement', 'Yutuq'),
        ('system', 'Tizim'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    icon = models.CharField(max_length=50, default='🔔')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    link = models.CharField(max_length=200, blank=True, help_text="URL to navigate when clicked")
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['user', 'is_read']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"

    @classmethod
    def get_unread_count(cls, user):
        """Get count of unread notifications for a user"""
        return cls.objects.filter(user=user, is_read=False).count()
    
    @classmethod
    def mark_all_read(cls, user):
        """Mark all unread notifications as read for a user"""
        count = cls.objects.filter(user=user, is_read=False).update(is_read=True)
        return count