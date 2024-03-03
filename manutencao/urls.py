from django.urls import path
from . import views


urlpatterns = [
path('home_manutecao/', views.home_manutencao, name='home_manutencao')
]