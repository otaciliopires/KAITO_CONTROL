from django.urls import path
from . import views

urlpatterns = [
    path('painel/', views.medicao_painel_ceq, name='medicao_painel_ceq'),
    path('obra/<int:obra_id>/', views.medicao_obra_home, name='medicao_obra_home'),
    path('obra/<int:obra_id>/caminhao/', views.medicao_caminhao_lista, name='medicao_caminhao_lista'),
    path('contrato/<int:contrato_id>/meses/', views.medicao_meses, name='medicao_meses'),
    path('contrato/<int:contrato_id>/<int:ano>/<int:mes>/', views.medicao_relatorio, name='medicao_relatorio'),
    path('contrato/<int:contrato_id>/<int:ano>/<int:mes>/fechar/', views.medicao_fechar_mes, name='medicao_fechar_mes'),
    path('contrato/<int:contrato_id>/<int:ano>/<int:mes>/boletim.pdf', views.medicao_boletim_pdf, name='medicao_boletim_pdf'),
]

# Rotas da medição de equipamentos, em arquivo próprio (bloco à parte, não mistura com as rotas de caminhão acima).
from .urls_equipamento import urlpatterns as _urlpatterns_equipamento  # noqa: E402
from .urls_equipamento_ceq import urlpatterns as _urlpatterns_equipamento_ceq  # noqa: E402
from .urls_equipamento_pdf import urlpatterns as _urlpatterns_equipamento_pdf  # noqa: E402
urlpatterns += _urlpatterns_equipamento + _urlpatterns_equipamento_ceq + _urlpatterns_equipamento_pdf
