
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('autenticacao.urls')),
    path('ceq/', include('controleCEQ.urls')),
    path('obra/', include('obras.urls')),
    path('manutencao/', include('manutencao.urls'))
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
