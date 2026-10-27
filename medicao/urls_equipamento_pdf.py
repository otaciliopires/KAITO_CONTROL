"""
Rotas de exportação em PDF da medição de equipamentos. Bloco próprio,
concatenado ao final de medicao/urls.py sem alterar nenhuma rota do fluxo
de caminhão.
"""
from django.urls import path

from . import views_equipamento_pdf as views

urlpatterns = [
    path('equip/medicao/<int:medicao_id>/boletim.pdf', views.medicao_equip_boletim_pdf, name='medicao_equip_boletim_pdf'),
    path('equip/ceq/periodo/<int:periodo_id>/resumo.pdf', views.medicao_equip_ceq_resumo_pdf, name='medicao_equip_ceq_resumo_pdf'),
]
