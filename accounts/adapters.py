"""
Custom adapters for django-allauth
Google OAuth orqali ro'yxatdan o'tganda UserProfile yaratish uchun
"""
import secrets
import string
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.adapter import DefaultAccountAdapter
from django.contrib.auth.models import User
from django.shortcuts import resolve_url
from django.conf import settings
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
        
        # Google orqali ro'yxatdan o'tganligini aniqlash
        is_google_signup = sociallogin.account.provider == 'google'
        
        # Parol generatsiya qilish (Google orqali ro'yxatdan o'tganda)
        generated_password = None
        if is_google_signup and not user.has_usable_password():
            # Xavfsiz parol generatsiya qilish
            alphabet = string.ascii_letters + string.digits + string.punctuation
            # 14 belgi uzunlikda parol
            generated_password = ''.join(secrets.choice(alphabet) for i in range(14))
            # Parolni user ga o'rnatish
            user.set_password(generated_password)
            user.save()
        
        # UserProfile yaratish yoki yangilash
        profile, created = UserProfile.objects.get_or_create(
            user=user,
            defaults={'is_manager': False}
        )
        
        # Google orqali ro'yxatdan o'tgan bo'lsa, flag va parolni saqlash
        if is_google_signup:
            profile.has_google_account = True
            if generated_password:
                profile.generated_password = generated_password
            profile.save()
        
        return user
    
    def get_login_redirect_url(self, request):
        """Google OAuth dan keyin qayerga o'tish"""
        # Custom login/register sahifalariga emas, to'g'ridan-to'g'ri dashboard ga
        return resolve_url(settings.LOGIN_REDIRECT_URL)


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
    
    def get_login_redirect_url(self, request):
        """Login dan keyin qayerga o'tish"""
        return resolve_url(settings.LOGIN_REDIRECT_URL)