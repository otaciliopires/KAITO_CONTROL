from django.contrib import admin
from .models import Ordem_Oficina, Servico_Oficina, Grupo_Servico, Funcionario, Servico_Terceirizado, Solicitacao, Socorro, Servico_Socorro, Preventiva, Ordem_Preventiva, Servico_Preventiva, Registro_Tempo_Servico, Pendencias


@admin.register(Ordem_Oficina)
class OrdemOficinaAdmin(admin.ModelAdmin):
    list_display = ('numero', 'equipamento', 'status', 'data_inicio', 'data_fim', 'tempo_total')
    list_filter = ('status', 'equipamento')
    search_fields = ('numero', 'equipamento__prefixo')
    date_hierarchy = 'data_inicio'


@admin.register(Servico_Oficina)
class ServicoOficinaAdmin(admin.ModelAdmin):
    list_display = ('numero', 'ordem_servico', 'grupo_servico', 'status', 'executante', 'data_inicio', 'data_fim')
    list_filter = ('status', 'grupo_servico', 'executante')
    search_fields = ('numero', 'descricao', 'ordem_servico__equipamento__prefixo')
    date_hierarchy = 'data_inicio'


@admin.register(Grupo_Servico)
class GrupoServicoAdmin(admin.ModelAdmin):
    list_display = ('grupo',)
    search_fields = ('grupo',)


@admin.register(Funcionario)
class FuncionarioAdmin(admin.ModelAdmin):
    list_display = ('nome', 'funcao')
    list_filter = ('funcao',)
    search_fields = ('nome',)


@admin.register(Servico_Terceirizado)
class ServicoTerceirizadoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'descricao')
    search_fields = ('nome', 'descricao')


@admin.register(Solicitacao)
class SolicitacaoAdmin(admin.ModelAdmin):
    list_display = ('insumo', 'equipamento', 'comprador', 'status', 'atendida', 'data_suprimentos', 'data_previsao')
    list_filter = ('status', 'atendida', 'comprador')
    search_fields = ('insumo', 'equipamento__prefixo')
    date_hierarchy = 'data_suprimentos'


@admin.register(Socorro)
class SocorroAdmin(admin.ModelAdmin):
    list_display = ('numero', 'obra', 'data_saida', 'data_chegada', 'tempo_socorro')
    list_filter = ('obra',)
    search_fields = ('numero',)
    filter_horizontal = ('mecanicos',)
    date_hierarchy = 'data_saida'


@admin.register(Servico_Socorro)
class Servico_SocorroAdmin(admin.ModelAdmin):
    list_display = ('equipamento', 'data_inicio', 'data_fim', 'mecanico', 'tempo_servico', 'resultado_servico')
    list_filter = ('resultado_servico', 'grupo_servico', 'mecanico')
    search_fields = ('equipamento__prefixo', 'descricao')
    date_hierarchy = 'data_inicio'


@admin.register(Preventiva)
class PreventivaAdmin(admin.ModelAdmin):
    list_display = ('numero', 'ordem', 'local', 'mecanico', 'data_emissao', 'assinatura_responsavel')
    list_filter = ('local', 'assinatura_responsavel', 'mecanico')
    search_fields = ('numero',)
    date_hierarchy = 'data_emissao'


@admin.register(Servico_Preventiva)
class ServicoPreventivaAdmin(admin.ModelAdmin):
    list_display = ('descricao', 'insumo', 'quantidade')
    search_fields = ('descricao', 'insumo')


@admin.register(Ordem_Preventiva)
class Servico_Ordem_PreventivaAdmin(admin.ModelAdmin):
    list_display = ('equipamento', 'periodo')
    list_filter = ('periodo', 'equipamento')
    search_fields = ('equipamento__prefixo',)
    filter_horizontal = ('servicos',)


@admin.register(Registro_Tempo_Servico)
class RegistroTempoServicoAdmin(admin.ModelAdmin):
    list_display = ('funcionario', 'tercerizado', 'data_inicial', 'data_final', 'tempo_servico')
    list_filter = ('funcionario', 'tercerizado')
    search_fields = ('descricao',)
    date_hierarchy = 'data_inicial'


@admin.register(Pendencias)
class PendenciasAdmin(admin.ModelAdmin):
    list_display = ('equipamento', 'status', 'situacao', 'data_inicio', 'data_fim')
    list_filter = ('status', 'situacao')
    search_fields = ('equipamento__prefixo', 'descricao')
    date_hierarchy = 'data_inicio'
