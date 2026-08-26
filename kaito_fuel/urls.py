
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from controleCEQ.api import api

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('autenticacao.urls')),
    path('ceq/', include('controleCEQ.urls')),
    path('obra/', include('obras.urls')),
    path('api/', api.urls)
]

if 'manutencao' in settings.INSTALLED_APPS:
    urlpatterns.append(path('manutencao/', include('manutencao.urls')))

if 'estoque' in settings.INSTALLED_APPS:
    urlpatterns.append(path('estoque/', include('estoque.urls')))

if 'medicao' in settings.INSTALLED_APPS:
    urlpatterns.append(path('medicao/', include('medicao.urls')))

if 'controle_diesel_obra' in settings.INSTALLED_APPS:
    urlpatterns.append(path('controle_diesel_obra/', include('controle_diesel_obra.urls')))

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
