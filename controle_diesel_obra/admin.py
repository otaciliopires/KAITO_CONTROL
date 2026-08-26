from django.contrib import admin

from .models import TanqueObra, EquipamentoObra, EntradaDiesel, SaidaDiesel


@admin.register(TanqueObra)
class TanqueObraAdmin(admin.ModelAdmin):
    list_display = ('obra', 'capacidade', 'estoque')
    search_fields = ('obra__nome',)


@admin.register(EquipamentoObra)
class EquipamentoObraAdmin(admin.ModelAdmin):
    list_display = ('prefixo', 'obra', 'descricao', 'tipo', 'unidade_medicao', 'contador_atual', 'ativo')
    list_filter = ('obra', 'tipo', 'unidade_medicao', 'ativo')
    search_fields = ('prefixo', 'descricao')


@admin.register(EntradaDiesel)
class EntradaDieselAdmin(admin.ModelAdmin):
    list_display = ('numero', 'obra', 'fornecedor', 'nota_fiscal', 'quantidade', 'preco_total', 'data_entrega')
    list_filter = ('obra',)
    search_fields = ('fornecedor', 'nota_fiscal', 'descricao')
    date_hierarchy = 'data_entrega'


@admin.register(SaidaDiesel)
class SaidaDieselAdmin(admin.ModelAdmin):
    list_display = ('numero', 'obra', 'equipamento', 'litros', 'data', 'operador')
    list_filter = ('obra', 'equipamento')
    search_fields = ('operador', 'observacao', 'equipamento__prefixo')
    date_hierarchy = 'data'
