from django.urls import path
from . import views

app_name = 'competitions'

urlpatterns = [
    path('', views.competition_list, name='list'),
    path('create/', views.competition_create, name='create'),
    path('<int:competition_id>/', views.competition_detail, name='detail'),
    path('<int:competition_id>/results/', views.competition_results, name='results'),
    path('<int:competition_id>/join/', views.competition_join, name='join'),
    path('<int:competition_id>/start/', views.competition_start, name='start'),
    path('<int:competition_id>/finish/', views.competition_finish, name='finish'),
    path('<int:competition_id>/play/<int:stage_number>/', views.competition_play, name='play'),
    path('<int:competition_id>/save-result/<int:stage_number>/', views.competition_save_result, name='save_result'),
    path('<int:competition_id>/certificate/', views.competition_certificate, name='certificate'),
    path('<int:competition_id>/certificate/<int:rank>/', views.competition_certificate, name='certificate_rank'),
]

