"""
Rotas da Central de Equipamentos (CEQ) para a medição de equipamentos.
Bloco próprio, name= prefixado medicao_equip_ceq_*. Concatenado ao final de
medicao/urls.py sem alterar nenhuma rota do fluxo de caminhão.
"""
from django.urls import path

from . import views_equipamento_ceq as views

urlpatterns = [
    path('equip/ceq/', views.medicao_equip_ceq_painel, name='medicao_equip_ceq_painel'),
    path('equip/ceq/localizacao/', views.medicao_equip_ceq_localizacao, name='medicao_equip_ceq_localizacao'),
    path('equip/ceq/periodo/<int:periodo_id>/obra/<int:obra_id>/', views.medicao_equip_ceq_obra, name='medicao_equip_ceq_obra'),
    path('equip/ceq/periodo/<int:periodo_id>/manutencao/', views.medicao_equip_ceq_manutencao, name='medicao_equip_ceq_manutencao'),
    path('equip/ceq/periodo/<int:periodo_id>/disposicao/', views.medicao_equip_ceq_disposicao, name='medicao_equip_ceq_disposicao'),
    path('equip/ceq/periodo/<int:periodo_id>/nova-direta/', views.medicao_equip_ceq_nova_medicao_direta, name='medicao_equip_ceq_nova_medicao_direta'),
    path('equip/ceq/periodo/<int:periodo_id>/fechar/', views.medicao_equip_ceq_fechar_periodo, name='medicao_equip_ceq_fechar_periodo'),
    path('equip/ceq/periodo/<int:periodo_id>/reabrir/', views.medicao_equip_ceq_reabrir_periodo, name='medicao_equip_ceq_reabrir_periodo'),

    path('equip/ceq/medicao/<int:medicao_id>/', views.medicao_equip_ceq_ajuste, name='medicao_equip_ceq_ajuste'),
    path('equip/ceq/medicao/<int:medicao_id>/aprovar/', views.medicao_equip_ceq_aprovar, name='medicao_equip_ceq_aprovar'),
    path('equip/ceq/medicao/<int:medicao_id>/ajustar/', views.medicao_equip_ceq_ajustar_devolver, name='medicao_equip_ceq_ajustar_devolver'),
    path('equip/ceq/medicao/<int:medicao_id>/lancar-manutencao/', views.medicao_equip_ceq_lancar_manutencao, name='medicao_equip_ceq_lancar_manutencao'),
    path('equip/ceq/medicao/<int:medicao_id>/lancar-disposicao/', views.medicao_equip_ceq_lancar_disposicao, name='medicao_equip_ceq_lancar_disposicao'),
    path('equip/ceq/medicao/<int:medicao_id>/reabrir/', views.medicao_equip_ceq_reabrir_medicao, name='medicao_equip_ceq_reabrir_medicao'),
    path('equip/ceq/medicao/<int:medicao_id>/fechar-direto/', views.medicao_equip_ceq_fechar_direto, name='medicao_equip_ceq_fechar_direto'),
]
