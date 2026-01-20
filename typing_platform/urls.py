"""
URL configuration for typing_platform project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('accounts/', include('allauth.urls')),  # Allauth URL'lar (google login/callback uchun) - birinchi bo'lsin
    path('accounts/', include('accounts.urls')),  # Sizning account URL'laringiz
    path('practice/', include('typing_practice.urls')),
    path('competitions/', include('competitions.urls')),
    path('leaderboard/', include('leaderboard.urls')),
    path('battles/', include('battles.urls')),
]

# Custom error handlers
handler404 = 'typing_platform.views.custom_404'
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)