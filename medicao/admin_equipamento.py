from django.contrib import admin

from .models_equipamento import (
    VinculoCaminhaoEquipamento,
    ValorMensalEquipamento,
    MotivoParada,
    PeriodoMedicaoEquipamento,
    MedicaoEquipamento,
    ApontamentoDiarioEquipamento,
    AjusteAdminEquipamento,
    LancamentoManutencaoEquipamento,
    LancamentoDisposicaoEquipamento,
    HistoricoMedicaoEquipamento,
)


class ValorMensalEquipamentoInline(admin.TabularInline):
    model = ValorMensalEquipamento
    extra = 0


@admin.register(VinculoCaminhaoEquipamento)
class VinculoCaminhaoEquipamentoAdmin(admin.ModelAdmin):
    list_display = ('equipamento', 'caminhao_abastecedor')
    search_fields = ('equipamento__prefixo', 'caminhao_abastecedor__identificacao')


@admin.register(ValorMensalEquipamento)
class ValorMensalEquipamentoAdmin(admin.ModelAdmin):
    list_display = ('equipamento', 'valor', 'vigente_desde')
    list_filter = ('equipamento',)
    search_fields = ('equipamento__prefixo',)
    ordering = ('-vigente_desde',)


@admin.register(MotivoParada)
class MotivoParadaAdmin(admin.ModelAdmin):
    list_display = ('descricao', 'destino_complemento', 'ativo')
    list_filter = ('destino_complemento', 'ativo')
    search_fields = ('descricao',)


@admin.register(PeriodoMedicaoEquipamento)
class PeriodoMedicaoEquipamentoAdmin(admin.ModelAdmin):
    list_display = ('ano', 'mes', 'data_inicio', 'data_fim', 'dias_do_mes', 'status')
    list_filter = ('status', 'ano')
    ordering = ('-ano', '-mes')


@admin.register(MedicaoEquipamento)
class MedicaoEquipamentoAdmin(admin.ModelAdmin):
    list_display = ('equipamento', 'obra', 'periodo', 'status', 'valor_aluguel_vigente', 'atualizado_em')
    list_filter = ('status', 'periodo', 'obra')
    search_fields = ('equipamento__prefixo', 'obra__nome')


@admin.register(ApontamentoDiarioEquipamento)
class ApontamentoDiarioEquipamentoAdmin(admin.ModelAdmin):
    list_display = ('medicao', 'data', 'tipo_dia', 'obra_do_dia', 'fracao_calculada', 'fracao_ajustada')
    list_filter = ('tipo_dia', 'obra_do_dia', 'motivo_parada')
    search_fields = ('medicao__equipamento__prefixo',)
    date_hierarchy = 'data'


@admin.register(AjusteAdminEquipamento)
class AjusteAdminEquipamentoAdmin(admin.ModelAdmin):
    list_display = ('medicao', 'obra', 'dias_apontados_obra', 'dias_aplicados_admin', 'autor', 'data')
    list_filter = ('obra',)
    search_fields = ('medicao__equipamento__prefixo', 'obra__nome')


@admin.register(LancamentoManutencaoEquipamento)
class LancamentoManutencaoEquipamentoAdmin(admin.ModelAdmin):
    list_display = ('medicao', 'dias', 'origem', 'autor', 'data_lancamento')
    list_filter = ('origem',)


@admin.register(LancamentoDisposicaoEquipamento)
class LancamentoDisposicaoEquipamentoAdmin(admin.ModelAdmin):
    list_display = ('medicao', 'dias', 'origem', 'autor', 'data_lancamento')
    list_filter = ('origem',)


@admin.register(HistoricoMedicaoEquipamento)
class HistoricoMedicaoEquipamentoAdmin(admin.ModelAdmin):
    list_display = ('medicao', 'campo', 'valor_anterior', 'valor_novo', 'usuario', 'data_hora')
    list_filter = ('campo',)
    search_fields = ('medicao__equipamento__prefixo',)
    date_hierarchy = 'data_hora'
