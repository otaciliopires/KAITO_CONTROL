from django.urls import path
from . import views

urlpatterns = [
    path('home/', views.home, name='home'),
    path('saidas/', views.saidas, name='saidas'),
    path('entradas/',views.entradas, name='entradas'),
    path('transferencias/', views.transferencias, name='transferencias'),
    path('obras/', views.obras, name='obras'),
    path('painel_obras/', views.painel_obras, name='painel_obras'),
    path('obras_ano/', views.obras_ano, name='obras_ano'),
    # path('ano/', views.ano, name='ano'),
    path('', views.importexcel, name='importexcel'),
    path('grafico_vunit/', views.grafico_vunit, name='grafico_vunit')
]
