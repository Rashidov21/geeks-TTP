"""
Custom adapters for django-allauth
Google OAuth orqali ro'yxatdan o'tganda UserProfile yaratish uchun
"""
import secrets
import string
import logging
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.adapter import DefaultAccountAdapter
from django.contrib.auth.models import User
from django.shortcuts import resolve_url
from django.conf import settings
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from .models import UserProfile, Notification

logger = logging.getLogger('typing_platform')


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
        # User allaqachon mavjudligini tekshirish (yangi user yoki eski)
        user_exists_before = False
        if sociallogin.user and sociallogin.user.pk:
            user_exists_before = True
        
        # Provider'ni saqlash (account saqlanishidan oldin)
        # sociallogin.state orqali provider'ni olish
        provider = None
        try:
            # Method 1: sociallogin.state orqali
            if hasattr(sociallogin, 'state') and sociallogin.state:
                if hasattr(sociallogin.state, 'provider'):
                    provider = sociallogin.state.provider
            # Method 2: sociallogin.account (agar mavjud bo'lsa)
            if not provider and hasattr(sociallogin, 'account') and sociallogin.account:
                provider = getattr(sociallogin.account, 'provider', None)
            # Method 3: sociallogin.provider
            if not provider and hasattr(sociallogin, 'provider'):
                provider = sociallogin.provider
        except (AttributeError, ObjectDoesNotExist) as e:
            logger.warning(f"Provider'ni aniqlashda xato: {e}")
        
        # User'ni saqlash (allauth o'zi account'ni saqlaydi)
        user = super().save_user(request, sociallogin, form)
        
        # Account saqlangandan keyin provider'ni qayta tekshirish
        if not provider:
            try:
                if hasattr(sociallogin, 'account') and sociallogin.account:
                    provider = getattr(sociallogin.account, 'provider', None)
            except (AttributeError, ObjectDoesNotExist):
                pass
        
        # Yangi user ekanligini aniqlash
        is_new_user = not user_exists_before
        
        # Transaction ichida ishlash (race condition'ni oldini olish uchun)
        try:
            with transaction.atomic():
                # Google orqali ro'yxatdan o'tganligini aniqlash
                is_google_signup = provider == 'google'
                
                # Parol generatsiya qilish (Google orqali ro'yxatdan o'tganda)
                generated_password = None
                if is_google_signup and not user.has_usable_password():
                    try:
                        # Xavfsiz parol generatsiya qilish
                        alphabet = string.ascii_letters + string.digits + string.punctuation
                        # 14 belgi uzunlikda parol
                        generated_password = ''.join(secrets.choice(alphabet) for i in range(14))
                        # Parolni user ga o'rnatish
                        user.set_password(generated_password)
                        user.save()
                    except Exception as e:
                        logger.error(f"Parol generatsiya qilishda xato: {e}")
                
                # UserProfile yaratish yoki yangilash
                # Signal allaqachon yaratgan bo'lishi mumkin, shuning uchun get_or_create ishlatamiz
                try:
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
                    
                    # Yangi Google user uchun notification yaratish
                    if is_new_user and is_google_signup and generated_password:
                        try:
                            Notification.objects.create(
                                user=user,
                                notification_type='system',
                                title='Parolni o\'zgartirish',
                                message='Siz Google orqali ro\'yxatdan o\'tdingiz. Xavfsizlik uchun parolni o\'zgartirishni tavsiya qilamiz. Profil sahifasida "Parolni o\'zgartirish" tugmasini bosing.',
                                icon='🔐',
                                link='/accounts/profile/'
                            )
                        except Exception as e:
                            logger.error(f"Notification yaratishda xato: {e}")
                except Exception as e:
                    logger.error(f"UserProfile yaratishda xato: {e}")
                    # Xato bo'lsa ham user saqlangan bo'ladi, shuning uchun davom etamiz
        except Exception as e:
            logger.error(f"Transaction ichida xato: {e}")
            # Xato bo'lsa ham user allaqachon saqlangan, shuning uchun davom etamiz
        
        # Yangi user bo'lsa, session'ga flag qo'shish (redirect uchun)
        if is_new_user:
            request.session['is_new_google_user'] = True
        
        return user
    
    def get_login_redirect_url(self, request):
        """Google OAuth dan keyin qayerga o'tish"""
        # Yangi Google user bo'lsa, profile page'ga redirect
        if request.session.get('is_new_google_user', False):
            # Flag'ni o'chirish
            del request.session['is_new_google_user']
            return resolve_url('accounts:profile')
        # Eski user bo'lsa, dashboard'ga
        return resolve_url(settings.LOGIN_REDIRECT_URL)
    
    def is_open_for_signup(self, request, sociallogin):
        """Social account orqali ro'yxatdan o'tishga ruxsat berish"""
        # Har doim ruxsat berish (continue page'ni o'tkazib yuborish uchun)
        return True
    
    def pre_social_login(self, request, sociallogin):
        """Social login'dan oldin ishlaydi - continue page'ni o'tkazib yuborish uchun"""
        # Continue page'ni o'tkazib yuborish - account'ni avtomatik ulash
        if sociallogin.is_existing:
            # Account allaqachon mavjud, ulash
            sociallogin.connect(request, sociallogin.user)
        return super().pre_social_login(request, sociallogin)


class CustomAccountAdapter(DefaultAccountAdapter):
    """Oddiy ro'yxatdan o'tish uchun adapter"""
    
    def save_user(self, request, user, form, commit=True):
        """User saqlash va UserProfile yaratish"""
        user = super().save_user(request, user, form, commit)
        
        # UserProfile yaratish (agar mavjud bo'lmasa)
        # Signal allaqachon yaratgan bo'lishi mumkin, shuning uchun get_or_create ishlatamiz
        if commit:
            try:
                UserProfile.objects.get_or_create(
                    user=user,
                    defaults={'is_manager': False}
                )
            except Exception as e:
                logger.error(f"UserProfile yaratishda xato: {e}")
        
        return user
    
    def get_login_redirect_url(self, request):
        """Login dan keyin qayerga o'tish"""
        return resolve_url(settings.LOGIN_REDIRECT_URL)