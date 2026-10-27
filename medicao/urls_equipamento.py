"""
Rotas da medição de equipamentos — bloco próprio, com name= prefixado
medicao_equip_*. Concatenado ao final de medicao/urls.py sem alterar
nenhuma rota do fluxo de caminhão.
"""
from django.urls import path

from . import views_equipamento as views

urlpatterns = [
    path('equip/<int:obra_id>/periodos/', views.medicao_equip_obra_periodos, name='medicao_equip_obra_periodos'),
    path('equip/<int:obra_id>/periodo/<int:periodo_id>/', views.medicao_equip_obra_periodo, name='medicao_equip_obra_periodo'),
    path('equip/<int:obra_id>/periodo/<int:periodo_id>/nova/', views.medicao_equip_obra_nova_medicao, name='medicao_equip_obra_nova_medicao'),

    path('equip/medicao/<int:medicao_id>/', views.medicao_equip_obra_medicao, name='medicao_equip_obra_medicao'),
    path('equip/medicao/<int:medicao_id>/salvar/', views.medicao_equip_obra_salvar, name='medicao_equip_obra_salvar'),
    path('equip/medicao/<int:medicao_id>/enviar/', views.medicao_equip_obra_enviar, name='medicao_equip_obra_enviar'),
    path('equip/medicao/<int:medicao_id>/confirmar/', views.medicao_equip_obra_confirmar, name='medicao_equip_obra_confirmar'),
    path('equip/medicao/<int:medicao_id>/contestar/', views.medicao_equip_obra_contestar, name='medicao_equip_obra_contestar'),
]
