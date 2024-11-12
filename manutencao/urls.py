from django.urls import path
from . import views



urlpatterns = [
path('home_manutencao/', views.home_manutencao, name='home_manutencao'),
path('osoficina/<int:id>/', views.servico_oficina, name='servico_oficina'),
path('socorro/<int:id>/', views.socorro, name='socorro'),
path('preventiva/<int:id>/', views.preventiva, name='preventiva'),
path('solicitacoes/', views.solicitacoes, name='solicitacoes'),
path('', views.atualizacao_horarios, name='atualizacao_horarios'),
path('analise_mecanicos/', views.analise_mecanicos, name='analise_mecanicos')
]