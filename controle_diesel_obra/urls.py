from django.urls import path

from . import views

urlpatterns = [
    path('<int:obra_id>/', views.home, name='cdo_home'),
    path('<int:obra_id>/operacoes/', views.operacoes, name='cdo_operacoes'),
    path('<int:obra_id>/importar/', views.importar_excel, name='cdo_importar'),

    path('<int:obra_id>/entradas/', views.entradas, name='cdo_entradas'),
    path('<int:obra_id>/entradas/<int:entrada_id>/editar/', views.entrada_editar, name='cdo_entrada_editar'),
    path('<int:obra_id>/entradas/<int:entrada_id>/excluir/', views.entrada_excluir, name='cdo_entrada_excluir'),

    path('<int:obra_id>/saidas/', views.saidas, name='cdo_saidas'),
    path('<int:obra_id>/saidas/<int:saida_id>/editar/', views.saida_editar, name='cdo_saida_editar'),
    path('<int:obra_id>/saidas/<int:saida_id>/excluir/', views.saida_excluir, name='cdo_saida_excluir'),

    path('<int:obra_id>/equipamentos/', views.equipamentos, name='cdo_equipamentos'),
    path('<int:obra_id>/equipamentos/<int:equip_id>/editar/', views.equipamento_editar, name='cdo_equipamento_editar'),
]
