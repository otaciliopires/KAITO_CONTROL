from django.contrib import admin
from .models import Solicitacao, ItemSolicitacao, EntradaEstoque


class ItemSolicitacaoInline(admin.TabularInline):
    model = ItemSolicitacao
    extra = 0
    fields = ('descricao', 'quantidade', 'status', 'fornecedor', 'preco_total')


@admin.register(Solicitacao)
class SolicitacaoAdmin(admin.ModelAdmin):
    list_display = ('id', 'solicitante', 'equipamento', 'data_solicitacao')
    list_filter = ('equipamento',)
    search_fields = ('solicitante__username', 'observacao')
    date_hierarchy = 'data_solicitacao'
    inlines = [ItemSolicitacaoInline]


@admin.register(ItemSolicitacao)
class ItemSolicitacaoAdmin(admin.ModelAdmin):
    list_display = ('descricao', 'solicitacao', 'quantidade', 'status', 'fornecedor', 'comprador', 'almoxarifado')
    list_filter = ('status',)
    search_fields = ('descricao', 'referencia', 'fornecedor', 'nota_fiscal')
    date_hierarchy = 'data_compra'


@admin.register(EntradaEstoque)
class EntradaEstoqueAdmin(admin.ModelAdmin):
    list_display = ('peca', 'quantidade', 'fornecedor', 'nota_fiscal', 'preco_total', 'usuario', 'data_entrada')
    list_filter = ('local_estoque',)
    search_fields = ('peca', 'referencia', 'fornecedor', 'nota_fiscal')
    date_hierarchy = 'data_entrada'
