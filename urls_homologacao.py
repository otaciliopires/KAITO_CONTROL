from django.contrib import admin
from django.urls import include, path
from controleCEQ import views_campo
from django.views.generic import RedirectView

admin.site.site_header = 'KAITO · HOMOLOGAÇÃO'
admin.site.site_title = 'KAITO · TESTE'
admin.site.index_title = 'Somente dados de teste'
urlpatterns = [
    path('', RedirectView.as_view(pattern_name='campo', permanent=False)),
    path('admin/', admin.site.urls),
    path('auth/', include('autenticacao.urls')),
    path('ceq/campo/', views_campo.app_campo, name='campo'),
    path('ceq/campo/sw.js', views_campo.service_worker, name='campo_sw'),
    path('ceq/campo/manifest.webmanifest', views_campo.manifest, name='campo_manifest'),
    path('ceq/campo/api/cadastros/', views_campo.cadastros, name='campo_cadastros'),
    path('ceq/campo/api/enviar/', views_campo.enviar, name='campo_enviar'),
]
