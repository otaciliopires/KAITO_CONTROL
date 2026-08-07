from django.contrib import admin

from .models import (
    CaminhaoAbastecedor, ValorMensalCaminhao, ParametroTaxaDiesel,
    ContratoMedicaoCaminhao, FechamentoMedicaoCaminhao,
)


class ValorMensalCaminhaoInline(admin.TabularInline):
    model = ValorMensalCaminhao
    extra = 0


@admin.register(CaminhaoAbastecedor)
class CaminhaoAbastecedorAdmin(admin.ModelAdmin):
    list_display = ('identificacao', 'tanque', 'marca', 'ativo')
    list_filter = ('ativo',)
    search_fields = ('identificacao', 'marca', 'tanque__prefixo')
    inlines = [ValorMensalCaminhaoInline]


@admin.register(ParametroTaxaDiesel)
class ParametroTaxaDieselAdmin(admin.ModelAdmin):
    list_display = ('percentual', 'vigente_desde')
    ordering = ('-vigente_desde',)


@admin.register(ContratoMedicaoCaminhao)
class ContratoMedicaoCaminhaoAdmin(admin.ModelAdmin):
    list_display = ('obra', 'caminhao', 'ativo', 'mes_referencia_inicial', 'numero_anterior')
    list_display_links = ('obra', 'caminhao')
    list_editable = ('mes_referencia_inicial',)
    list_filter = ('ativo', 'caminhao')
    search_fields = ('obra__nome', 'caminhao__identificacao')


@admin.register(FechamentoMedicaoCaminhao)
class FechamentoMedicaoCaminhaoAdmin(admin.ModelAdmin):
    list_display = ('contrato', 'ano', 'mes', 'fechado_em', 'fechado_por')
    list_filter = ('ano', 'contrato')
    ordering = ('-ano', '-mes')
