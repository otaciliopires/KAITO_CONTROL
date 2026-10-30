from django.urls import path
from . import views
from . import views_campo
from .api import api

urlpatterns = [
    path('campo/', views_campo.app_campo, name='campo'),
    path('campo/sw.js', views_campo.service_worker, name='campo_sw'),
    path('campo/manifest.webmanifest', views_campo.manifest, name='campo_manifest'),
    path('campo/api/cadastros/', views_campo.cadastros, name='campo_cadastros'),
    path('campo/api/enviar/', views_campo.enviar, name='campo_enviar'),
    path('home/', views.home, name='home'),
    path('operacoes/', views.operacoes, name='operacoes'),
    path('saidas/', views.saidas, name='saidas'),
    path('entradas/',views.entradas, name='entradas'),
    path('transferencias/', views.transferencias, name='transferencias'),
    path('obras/', views.obras, name='obras'),
    path('painel_obras/', views.painel_obras, name='painel_obras'),
    path('obras_ano/', views.obras_ano, name='obras_ano'),
    path('', views.importexcel, name='importexcel'),
    path('grafico_vunit/', views.grafico_vunit, name='grafico_vunit'),
    path('relatorio/', views.relatorio, name='relatorio'),
    path('pdf_relatorio/<str:mes_atual>/', views.pdf_relatorio, name='pdf_relatorio'),
    path('saidas_pdf/', views.saidas_pdf, name='saidas_pdf'),
    path('entradas_pdf/', views.entradas_pdf, name='entradas_pdf'),

]
