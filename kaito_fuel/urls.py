
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
    path('manutencao/', include('manutencao.urls')),
    path('estoque/', include('estoque.urls')),
    path('api/', api.urls)
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) 
