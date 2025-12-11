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
