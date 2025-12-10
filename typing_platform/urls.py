"""
URL configuration for typing_platform project.
"""
from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('accounts/', include('accounts.urls')),
    path('practice/', include('typing_practice.urls')),
    path('competitions/', include('competitions.urls')),
    path('leaderboard/', include('leaderboard.urls')),
]

# Custom error handlers
handler404 = 'typing_platform.views.custom_404'
