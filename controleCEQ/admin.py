from django.contrib import admin
from .models import Tanque, Abastecimento, Entrada, Transferencia, Saldo


@admin.register(Tanque)
class TanqueAdmin(admin.ModelAdmin):
    list_display = ('prefixo', 'tipo', 'capacidade', 'estoque', 'contador')
    list_filter = ('tipo',)
    search_fields = ('prefixo', 'descricao')


@admin.register(Abastecimento)
class AbastecimentoAdmin(admin.ModelAdmin):
    list_display = ('equipamento', 'obra', 'litros', 'data', 'operador', 'status', 'observacao')
    list_filter = ('obra', 'tanque', 'lubrificacao', 'status')
    search_fields = ('equipamento__prefixo', 'operador', 'observacao')
    date_hierarchy = 'data'


@admin.register(Entrada)
class EntradaAdmin(admin.ModelAdmin):
    list_display = ('obra', 'tanque', 'fornecedor', 'nota_fiscal', 'quantidade', 'preco_total', 'data_entrega')
    list_filter = ('obra', 'tanque')
    search_fields = ('fornecedor', 'nota_fiscal', 'descricao')
    date_hierarchy = 'data_entrega'


@admin.register(Transferencia)
class TransferenciaAdmin(admin.ModelAdmin):
    list_display = ('fixo', 'movel', 'litros', 'colaborador', 'data')
    list_filter = ('fixo', 'movel')
    date_hierarchy = 'data'


@admin.register(Saldo)
class SaldoAdmin(admin.ModelAdmin):
    list_display = ('ano', 'quantidade')
    list_filter = ('ano',)
