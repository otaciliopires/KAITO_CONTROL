from django.urls import path
from . import views

urlpatterns = [
    path('<int:id>/', views.obra, name='obra'),
    path('status/<int:id>/', views.status, name='status'),
    path('comentario/<int:id>', views.comentario, name='comentario'),
    path('exportexcel/', views.exportexcel, name='exportexcel'),
    path('testegrafico/', views.testegrafico, name='testegrafico'),
    path('rederiza_grafico/', views.renderiza_grafico, name='rederiza_grafico'),
    path('lista_obras/', views.lista_obras, name='lista_obras')

]