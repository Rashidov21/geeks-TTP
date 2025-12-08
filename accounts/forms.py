from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm


class CustomUserCreationForm(UserCreationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 bg-gray-50 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-secondary focus:border-secondary transition-all duration-300 hover:bg-white hover:border-gray-400 placeholder:text-gray-400 text-primary',
            'placeholder': 'Foydalanuvchi nomini kiriting'
        })
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 bg-gray-50 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-secondary focus:border-secondary transition-all duration-300 hover:bg-white hover:border-gray-400 placeholder:text-gray-400 text-primary',
            'placeholder': 'Parolni kiriting'
        })
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 bg-gray-50 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-secondary focus:border-secondary transition-all duration-300 hover:bg-white hover:border-gray-400 placeholder:text-gray-400 text-primary',
            'placeholder': 'Parolni qayta kiriting'
        })
    )


class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 bg-gray-50 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-secondary focus:border-secondary transition-all duration-300 hover:bg-white hover:border-gray-400 placeholder:text-gray-400 text-primary',
            'placeholder': 'Foydalanuvchi nomini kiriting'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 bg-gray-50 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-secondary focus:border-secondary transition-all duration-300 hover:bg-white hover:border-gray-400 placeholder:text-gray-400 text-primary',
            'placeholder': 'Parolni kiriting'
        })
    )

