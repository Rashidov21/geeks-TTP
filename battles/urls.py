from django.urls import path
from . import views

app_name = 'battles'

urlpatterns = [
    path('', views.battle_list, name='list'),
    path('create/', views.battle_create, name='create'),
    path('<int:battle_id>/', views.battle_detail, name='detail'),
    path('<int:battle_id>/join/', views.battle_join, name='join'),
    path('<int:battle_id>/play/', views.battle_play, name='play'),
    path('<int:battle_id>/save-result/', views.battle_save_result, name='save_result'),
]

