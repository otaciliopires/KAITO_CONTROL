from django.urls import path
from . import views

urlpatterns = [
    path('', views.estoque_home, name='estoque_home'),
    path('nova/', views.nova_solicitacao, name='nova_solicitacao'),
    path('minhas/', views.minhas_solicitacoes, name='minhas_solicitacoes'),
    path('comprar/', views.comprar_lista, name='comprar_lista'),
    path('comprar/<int:item_id>/', views.comprar_item, name='comprar_item'),
    path('receber/', views.receber_lista, name='receber_lista'),
    path('receber/<int:item_id>/', views.receber_item, name='receber_item'),
    path('retirar/<int:item_id>/', views.retirar_item, name='retirar_item'),
    path('entrada/', views.dar_entrada, name='dar_entrada'),
    path('fluxo/', views.fluxo, name='fluxo'),
]
