from django.urls import path
from . import views



urlpatterns = [
path('home_manutencao/', views.home_manutencao, name='home_manutencao'),
path('osoficina/<int:id>/', views.servico_oficina, name='servico_oficina')
]