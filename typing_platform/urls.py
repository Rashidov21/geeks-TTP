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
    # Legal pages
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    path('terms-of-service/', views.terms_of_service, name='terms_of_service'),
    path('contact/', views.contact, name='contact'),
    # SEO
    path('robots.txt', views.robots_txt, name='robots_txt'),
    path('sitemap.xml', views.sitemap_xml, name='sitemap_xml'),
    # Allauth URL'lar - allauth dan oldin (standart Google login URL'ini ishlatish uchun)
    path('accounts/', include('allauth.urls')),
    # Custom accounts URL'lar - allauth dan keyin
    path('accounts/', include('accounts.urls')),
    path('practice/', include('typing_practice.urls')),
    path('competitions/', include('competitions.urls')),
    path('leaderboard/', include('leaderboard.urls')),
    path('battles/', include('battles.urls')),
    path('captcha/', include('captcha.urls')),
]

# Custom error handlers
handler404 = 'typing_platform.views.custom_404'
handler500 = 'typing_platform.views.custom_500'
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)