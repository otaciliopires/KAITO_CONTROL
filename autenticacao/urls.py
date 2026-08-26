from django.urls import path
from autenticacao import views

urlpatterns = [
    path('login/', views.login, name='login'),
    path('sair/', views.sair, name='sair')
]
