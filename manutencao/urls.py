from django.urls import path
from . import views



urlpatterns = [

path('homemanutencao/', views.home_manutencao, name='homemanutencao')


]