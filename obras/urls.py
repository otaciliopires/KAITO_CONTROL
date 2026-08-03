from django.urls import path
from . import views

urlpatterns = [
    path('<int:id>/', views.obra, name='obra'),
    path('<int:id>/entradas/', views.obra_entradas, name='obra_entradas'),
    path('<int:id>/abastecimentos/', views.obra_abastecimentos, name='obra_abastecimentos'),
    path('reportar_problema/<int:id>/', views.reportar_problema, name='reportar_problema'),
    path('status/<int:id>/', views.status, name='status'),
    path('comentario/<int:id>', views.comentario, name='comentario'),
    path('exportexcel/<int:id>', views.exportexcel, name='exportexcel'),
    path('testegrafico/', views.testegrafico, name='testegrafico'),
    path('rederiza_grafico/', views.renderiza_grafico, name='rederiza_grafico'),
    path('lista_obras/', views.lista_obras, name='lista_obras')

]