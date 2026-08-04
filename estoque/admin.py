from django.contrib import admin
from .models import Solicitacao, ItemSolicitacao, EntradaEstoque

admin.site.register(Solicitacao)
admin.site.register(ItemSolicitacao)
admin.site.register(EntradaEstoque)
