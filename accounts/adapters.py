"""
Custom adapters for django-allauth
Google OAuth orqali ro'yxatdan o'tganda UserProfile yaratish uchun
"""
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.adapter import DefaultAccountAdapter
from django.contrib.auth.models import User
from .models import UserProfile


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """Google login'dan keyin UserProfile yaratish"""
    
    def populate_user(self, request, sociallogin, data):
        """User ma'lumotlarini to'ldirish"""
        user = super().populate_user(request, sociallogin, data)
        
        # Username'ni email'dan olish (agar bo'sh bo'lsa)
        if not user.username:
            email = data.get('email', '')
            if email:
                # Email'dan username yaratish
                username = email.split('@')[0]
                # Username unique bo'lishi kerak
                counter = 1
                original_username = username
                while User.objects.filter(username=username).exists():
                    username = f"{original_username}{counter}"
                    counter += 1
                user.username = username
        
        # First name va last name
        if not user.first_name:
            user.first_name = data.get('given_name', '') or data.get('first_name', '')
        if not user.last_name:
            user.last_name = data.get('family_name', '') or data.get('last_name', '')
        
        return user
    
    def save_user(self, request, sociallogin, form=None):
        """User saqlash va UserProfile yaratish"""
        user = super().save_user(request, sociallogin, form)
        
        # UserProfile yaratish (agar mavjud bo'lmasa)
        if not UserProfile.objects.filter(user=user).exists():
            UserProfile.objects.create(
                user=user,
                is_manager=False,
            )
        
        return user


class CustomAccountAdapter(DefaultAccountAdapter):
    """Oddiy ro'yxatdan o'tish uchun adapter"""
    
    def save_user(self, request, user, form, commit=True):
        """User saqlash va UserProfile yaratish"""
        user = super().save_user(request, user, form, commit)
        
        # UserProfile yaratish (agar mavjud bo'lmasa)
        if commit and not UserProfile.objects.filter(user=user).exists():
            UserProfile.objects.create(
                user=user,
                is_manager=False,
            )
        
        return user
