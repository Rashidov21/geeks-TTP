from django.urls import path
from . import views

app_name = 'typing_practice'

urlpatterns = [
    path('', views.index, name='index'),
    path('text/settings/', views.text_settings, name='text_settings'),
    path('text/<str:difficulty>/', views.text_practice, name='text_practice'),
    path('code/<str:language>/', views.code_practice, name='code_practice'),
    path('save-result/', views.save_result, name='save_result'),
]

