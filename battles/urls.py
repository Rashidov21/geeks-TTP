from django.urls import path
from . import views

app_name = 'battles'

urlpatterns = [
    path('', views.battle_list, name='list'),
    path('create/', views.battle_create, name='create'),
    path('quick-match/', views.battle_quick_match, name='quick_match'),
    path('invite/', views.battle_invite, name='invite'),
    path('invitations/<int:invitation_id>/', views.battle_invitation_respond, name='invitation_respond'),
    path('<int:battle_id>/', views.battle_detail, name='detail'),
    path('<int:battle_id>/join/', views.battle_join, name='join'),
    path('<int:battle_id>/play/', views.battle_play, name='play'),
    path('<int:battle_id>/rematch/', views.battle_rematch, name='rematch'),
    path('<int:battle_id>/save-result/', views.battle_save_result, name='save_result'),
    path('<int:battle_id>/opponent-progress/', views.battle_opponent_progress, name='opponent_progress'),
]

