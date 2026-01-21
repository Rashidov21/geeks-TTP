from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordResetForm, SetPasswordForm
from django.core.exceptions import ValidationError
from .models import UserProfile
import re
from captcha.fields import CaptchaField



class CustomUserCreationForm(UserCreationForm):
    username = forms.CharField(
        label='Foydalanuvchi nomi',
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 bg-gray-50 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary transition-all duration-300 hover:bg-white hover:border-gray-400 placeholder:text-gray-400 text-primary',
            'placeholder': 'Foydalanuvchi nomini kiriting'
        }),
        help_text='150 belgidan oshmasligi kerak. Faqat harflar, raqamlar va @/./+/-/_ belgilari.'
    )
    password1 = forms.CharField(
        label='Parol',
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 pr-12 bg-gray-50 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary transition-all duration-300 hover:bg-white hover:border-gray-400 placeholder:text-gray-400 text-primary',
            'placeholder': 'Parolni kiriting',
            'id': 'id_password1'
        }),
        help_text='Parol kamida 6 belgidan iborat bo\'lishi kerak.'
    )
    password2 = forms.CharField(
        label='Parolni tasdiqlash',
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 pr-12 bg-gray-50 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary transition-all duration-300 hover:bg-white hover:border-gray-400 placeholder:text-gray-400 text-primary',
            'placeholder': 'Parolni qayta kiriting',
            'id': 'id_password2'
        }),
        help_text='Tasdiqlash uchun parolni qayta kiriting.'
    )
    
    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')
        if password1:
            # Faqat minimal uzunlik talab qilish - oson va qulay
            if len(password1) < 6:
                raise ValidationError('Parol kamida 6 belgidan iborat bo\'lishi kerak.')
        return password1
    
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        
        if password1 and password2 and password1 != password2:
            raise ValidationError({
                'password2': ValidationError('Parollar mos kelmaydi.')
            })
        
        return cleaned_data
    
    error_messages = {
        'password_mismatch': 'Parollar mos kelmaydi.',
        'password_too_short': 'Parol juda qisqa.',
        'password_too_common': 'Parol juda oddiy.',
        'password_entirely_numeric': 'Parol to\'liq raqamlardan iborat bo\'lmasligi kerak.',
    }


class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        label='Foydalanuvchi nomi',
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 bg-gray-50 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary transition-all duration-300 hover:bg-white hover:border-gray-400 placeholder:text-gray-400 text-primary',
            'placeholder': 'Foydalanuvchi nomini kiriting'
        })
    )
    password = forms.CharField(
        label='Parol',
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 bg-gray-50 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary transition-all duration-300 hover:bg-white hover:border-gray-400 placeholder:text-gray-400 text-primary',
            'placeholder': 'Parolni kiriting'
        })
    )
    captcha = CaptchaField()
    
    error_messages = {
        'invalid_login': 'Foydalanuvchi nomi yoki parol noto\'g\'ri.',
        'inactive': 'Bu hisob faol emas.',
    }


class UserProfileForm(forms.ModelForm):
    first_name = forms.CharField(
        label='Ism',
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 bg-gray-50 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary text-primary',
            'placeholder': 'Ism'
        })
    )
    last_name = forms.CharField(
        label='Familiya',
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 bg-gray-50 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary text-primary',
            'placeholder': 'Familiya'
        })
    )
    
    class Meta:
        model = UserProfile
        fields = ['image', 'bio', 'address', 'phone']
        widgets = {
            'image': forms.FileInput(attrs={
                'class': 'w-full px-4 py-2 bg-gray-50 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary text-primary',
                'accept': 'image/*'
            }),
            'bio': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 bg-gray-50 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary text-primary',
                'rows': 4,
                'placeholder': 'O\'zingiz haqingizda yozing...'
            }),
            'address': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 bg-gray-50 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary text-primary',
                'placeholder': 'Manzil'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 bg-gray-50 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary text-primary',
                'placeholder': 'Telefon raqami'
            }),
        }
        labels = {
            'image': 'Rasm',
            'bio': 'Bio',
            'address': 'Manzil',
            'phone': 'Telefon raqami',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name


class PasswordResetRequestForm(PasswordResetForm):
    """Password reset so'rov formasi"""
    email = forms.EmailField(
        label='Email manzil',
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 bg-gray-50 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary transition-all duration-300 hover:bg-white hover:border-gray-400 placeholder:text-gray-400 text-primary',
            'placeholder': 'Email manzilingizni kiriting'
        })
    )
    
    error_messages = {
        'invalid_email': 'Noto\'g\'ri email manzil.',
    }


class PasswordResetConfirmForm(SetPasswordForm):
    """Yangi parol o'rnatish formasi"""
    new_password1 = forms.CharField(
        label='Yangi parol',
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 pr-12 bg-gray-50 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary transition-all duration-300 hover:bg-white hover:border-gray-400 placeholder:text-gray-400 text-primary',
            'placeholder': 'Yangi parolni kiriting',
            'id': 'id_new_password1'
        }),
        help_text='Parol kamida 8 belgidan iborat bo\'lishi kerak.'
    )
    new_password2 = forms.CharField(
        label='Parolni tasdiqlash',
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 pr-12 bg-gray-50 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary transition-all duration-300 hover:bg-white hover:border-gray-400 placeholder:text-gray-400 text-primary',
            'placeholder': 'Parolni qayta kiriting',
            'id': 'id_new_password2'
        }),
        help_text='Tasdiqlash uchun parolni qayta kiriting.'
    )
    
    error_messages = {
        'password_mismatch': 'Parollar mos kelmaydi.',
        'password_too_short': 'Parol juda qisqa.',
        'password_too_common': 'Parol juda oddiy.',
        'password_entirely_numeric': 'Parol to\'liq raqamlardan iborat bo\'lmasligi kerak.',
    }
