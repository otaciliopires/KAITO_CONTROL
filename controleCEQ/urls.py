from django.urls import path
from . import views
from . import views_campo, views_relatorios, views_saidas, views_transferencias, views_movimentos
from .api import api
from . import views_validacao_campo

urlpatterns = [
    path('campo/', views_campo.app_campo, name='campo'),
    path('campo/sw.js', views_campo.service_worker, name='campo_sw'),
    path('campo/manifest.webmanifest', views_campo.manifest, name='campo_manifest'),
    path('campo/api/cadastros/', views_campo.cadastros, name='campo_cadastros'),
    path('campo/api/validar-responsavel/', views_validacao_campo.enviar_validacao, name='campo_validacao_responsavel'),
    path('campo/api/enviar/', views_campo.enviar, name='campo_enviar'),
    path('home/', views.home, name='home'),
    path('operacoes/', views.operacoes, name='operacoes'),
    path('saidas/', views_saidas.saidas, name='saidas'),
    path('saidas/equipamentos/', views_saidas.equipamentos_saidas, name='saidas_equipamentos'),
    path('entradas/',views_movimentos.entradas, name='entradas'),
    path('transferencias/', views_movimentos.transferencias, name='transferencias'),
    path('obras/', views.obras, name='obras'),
    path('painel_obras/', views.painel_obras, name='painel_obras'),
    path('obras_ano/', views.obras_ano, name='obras_ano'),
    path('', views.importexcel, name='importexcel'),
    path('grafico_vunit/', views.grafico_vunit, name='grafico_vunit'),
    path('relatorio/', views_relatorios.relatorio, name='relatorio'),
    path('relatorio/pdf/', views_relatorios.relatorio_pdf, name='relatorio_pdf'),
    path('pdf_relatorio/<str:mes_atual>/', views.pdf_relatorio, name='pdf_relatorio'),
    path('saidas_pdf/', views_saidas.saidas_pdf, name='saidas_pdf'),
    path('transferencias_pdf/', views_movimentos.transferencias_pdf, name='transferencias_pdf'),
    path('entradas/opcoes/', views_movimentos.entradas_opcoes, name='entradas_opcoes'),
    path('transferencias/opcoes/', views_movimentos.transferencias_opcoes, name='transferencias_opcoes'),
    path('entradas_pdf/', views_movimentos.entradas_pdf, name='entradas_pdf'),

]
