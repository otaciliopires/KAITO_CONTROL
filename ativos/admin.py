from django.contrib import admin
from .models import Obras, Equipamentos


@admin.register(Obras)
class ObrasAdmin(admin.ModelAdmin):
    list_display = ('nome', 'status', 'saldo', 'endereço', 'distancia')
    list_filter = ('status',)
    search_fields = ('nome', 'endereço')
    filter_horizontal = ('usuario',)


@admin.register(Equipamentos)
class EquipamentosAdmin(admin.ModelAdmin):
    list_display = ('prefixo', 'descricao', 'tipo', 'proprietario', 'horímetro', 'unidade_medicao', 'elegivel_medicao')
    list_filter = ('tipo', 'proprietario', 'unidade_medicao', 'elegivel_medicao')
    search_fields = ('prefixo', 'descricao')
