"""
Medição mensal de equipamentos — rateio de aluguel por obra, dia a dia.

Módulo isolado do fluxo de medição de caminhão (ver models.py: CaminhaoAbastecedor,
ValorMensalCaminhao, ParametroTaxaDiesel, ContratoMedicaoCaminhao,
FechamentoMedicaoCaminhao). Nenhum model, cálculo ou view daqui reaproveita ou
altera nada do fluxo de caminhão — só existe uma tabela de vínculo
(VinculoCaminhaoEquipamento) para permitir excluir caminhões do cadastro geral
de equipamentos, sem tocar em CaminhaoAbastecedor.
"""
from django.conf import settings
from django.db import models

from ativos.models import Equipamentos, Obras


class VinculoCaminhaoEquipamento(models.Model):
    """Liga um Equipamentos ao CaminhaoAbastecedor correspondente, exclusivamente
    para a medição de equipamento saber quem excluir do cadastro geral. Não é
    lido nem escrito por nenhuma lógica do fluxo de caminhão."""

    equipamento = models.OneToOneField(
        Equipamentos, on_delete=models.CASCADE, related_name='vinculo_caminhao'
    )
    caminhao_abastecedor = models.OneToOneField(
        'medicao.CaminhaoAbastecedor', on_delete=models.CASCADE, related_name='vinculo_equipamento'
    )

    def __str__(self):
        return f"{self.equipamento.prefixo} = {self.caminhao_abastecedor.identificacao}"


class ValorMensalEquipamento(models.Model):
    """Histórico de valor de aluguel mensal vigente por equipamento. Independente
    de ValorMensalCaminhao — o histórico importa para reprocessar meses fechados
    com o valor da época."""

    equipamento = models.ForeignKey(
        Equipamentos, on_delete=models.CASCADE, related_name='valores_mensais_medicao'
    )
    valor = models.DecimalField(max_digits=12, decimal_places=2)
    vigente_desde = models.DateField()

    class Meta:
        ordering = ['-vigente_desde']

    def __str__(self):
        return f"{self.equipamento.prefixo} - R$ {self.valor} desde {self.vigente_desde}"


class MotivoParada(models.Model):
    DESTINO_MANUTENCAO = 'MANUTENCAO'
    DESTINO_DISPOSICAO = 'DISPOSICAO'
    DESTINO_CHOICES = (
        (DESTINO_MANUTENCAO, 'Manutenção'),
        (DESTINO_DISPOSICAO, 'À disposição'),
    )

    descricao = models.CharField(max_length=100)
    destino_complemento = models.CharField(max_length=10, choices=DESTINO_CHOICES)
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Motivo de parada (equipamento)'
        verbose_name_plural = 'Motivos de parada (equipamento)'

    def __str__(self):
        return self.descricao


class PeriodoMedicaoEquipamento(models.Model):
    STATUS_ABERTO = 'ABERTO'
    STATUS_FECHADO = 'FECHADO'
    STATUS_CHOICES = (
        (STATUS_ABERTO, 'Aberto'),
        (STATUS_FECHADO, 'Fechado'),
    )

    ano = models.IntegerField()
    mes = models.IntegerField()
    data_inicio = models.DateField()
    data_fim = models.DateField()
    dias_do_mes = models.IntegerField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_ABERTO)

    class Meta:
        unique_together = ('ano', 'mes')
        ordering = ['-ano', '-mes']

    def __str__(self):
        return f"{self.mes:02d}/{self.ano}"


class MedicaoEquipamento(models.Model):
    STATUS_RASCUNHO = 'RASCUNHO'
    STATUS_ENVIADA = 'ENVIADA'
    STATUS_EM_ANALISE = 'EM_ANALISE'
    STATUS_DEVOLVIDA = 'DEVOLVIDA'
    STATUS_FECHADA = 'FECHADA'
    STATUS_CHOICES = (
        (STATUS_RASCUNHO, 'Rascunho'),
        (STATUS_ENVIADA, 'Enviada'),
        (STATUS_EM_ANALISE, 'Em análise'),
        (STATUS_DEVOLVIDA, 'Devolvida'),
        (STATUS_FECHADA, 'Fechada'),
    )

    periodo = models.ForeignKey(
        PeriodoMedicaoEquipamento, on_delete=models.PROTECT, related_name='medicoes_equipamento'
    )
    equipamento = models.ForeignKey(Equipamentos, on_delete=models.PROTECT, related_name='medicoes_equipamento')
    obra = models.ForeignKey(
        Obras, on_delete=models.PROTECT, related_name='medicoes_equipamento_responsavel',
        null=True, blank=True,
        help_text="Em branco = medição aberta direto pela Central, sem obra envolvida "
                   "(equipamento parado em manutenção/à disposição o período inteiro).",
    )
    valor_aluguel_vigente = models.DecimalField(
        max_digits=12, decimal_places=2,
        help_text="Snapshot do ValorMensalEquipamento vigente na abertura da medição.",
    )
    operador = models.CharField(max_length=50, blank=True, default="")
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=STATUS_RASCUNHO)

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    enviada_em = models.DateTimeField(null=True, blank=True)
    enviada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='medicoes_equip_enviadas',
    )

    analisada_em = models.DateTimeField(null=True, blank=True)
    analisada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='medicoes_equip_analisadas',
    )

    devolvida_em = models.DateTimeField(null=True, blank=True)
    devolvida_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='medicoes_equip_devolvidas',
    )

    fechada_em = models.DateTimeField(null=True, blank=True)
    fechada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='medicoes_equip_fechadas',
    )

    reaberta_em = models.DateTimeField(null=True, blank=True)
    reaberta_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='medicoes_equip_reabertas',
    )

    class Meta:
        # Uma medição por obra: a mesma máquina pode ter uma medição própria
        # aberta por cada obra que a usou no período (ver abrir_medicao em
        # servicos_equipamento.py). obra=None (medição direta da Central) é
        # tratado à parte por essa mesma função — nunca coexiste com uma
        # medição de obra no mesmo período/equipamento.
        unique_together = ('periodo', 'equipamento', 'obra')

    def __str__(self):
        obra_nome = self.obra.nome if self.obra_id else 'Central (sem obra)'
        return f"{self.equipamento.prefixo} - {obra_nome} - {self.periodo}"


class ApontamentoDiarioEquipamento(models.Model):
    TIPO_TRABALHO = 'TRABALHO'
    TIPO_MANUTENCAO = 'MANUTENCAO'
    TIPO_DISPOSICAO = 'DISPOSICAO'
    TIPO_CHOICES = (
        (TIPO_TRABALHO, 'Trabalho'),
        (TIPO_MANUTENCAO, 'Manutenção'),
        (TIPO_DISPOSICAO, 'À disposição'),
    )

    medicao = models.ForeignKey(MedicaoEquipamento, on_delete=models.CASCADE, related_name='apontamentos')
    data = models.DateField()
    contador_inicial = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    contador_final = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text="Em branco = dia ainda não preenchido pela obra.",
    )
    tempo_parada_horas = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    motivo_parada = models.ForeignKey(
        MotivoParada, on_delete=models.PROTECT, null=True, blank=True,
        related_name='apontamentos_equipamento',
    )
    obra_do_dia = models.ForeignKey(
        Obras, on_delete=models.PROTECT, related_name='apontamentos_diarios_equipamento'
    )
    tipo_dia = models.CharField(
        max_length=10, choices=TIPO_CHOICES, null=True, blank=True,
        help_text="Derivado automaticamente no save a partir da fração e do motivo — nunca escolhido manualmente.",
    )
    fracao_calculada = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    fracao_ajustada = models.DecimalField(
        max_digits=3, decimal_places=2, null=True, blank=True,
        help_text="Override exclusivo da Central (CEQ), nunca preenchido pela obra.",
    )
    observacoes = models.TextField(blank=True, default="")

    class Meta:
        unique_together = ('medicao', 'data')
        ordering = ['data']

    def __str__(self):
        return f"{self.medicao} - {self.data}"

    @property
    def preenchido(self):
        """Dia já recebeu leitura da obra (contador_final informado)."""
        return self.contador_final is not None

    @property
    def variacao_contador(self):
        """Contador final - contador inicial. Só representa horas trabalhadas
        quando o equipamento é medido por horímetro (ver
        Equipamentos.unidade_medicao); para odômetro é distância. A fração real
        é sempre recalculada em calculos_equipamento.py, nunca lida daqui."""
        if self.contador_final is None or self.contador_inicial is None:
            return None
        return self.contador_final - self.contador_inicial

    @property
    def fracao(self):
        return self.fracao_ajustada if self.fracao_ajustada is not None else self.fracao_calculada


class AjusteAdminEquipamento(models.Model):
    """Ajuste da Central sobre o total apurado de uma obra dentro de uma medição.
    Nunca sobrescreve o valor original da obra — os dois lados ficam guardados
    para auditoria."""

    medicao = models.ForeignKey(MedicaoEquipamento, on_delete=models.CASCADE, related_name='ajustes_admin')
    obra = models.ForeignKey(Obras, on_delete=models.PROTECT, related_name='ajustes_admin_equipamento')
    dias_apontados_obra = models.DecimalField(max_digits=5, decimal_places=2)
    dias_aplicados_admin = models.DecimalField(max_digits=5, decimal_places=2)
    justificativa = models.TextField()
    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='ajustes_admin_equipamento'
    )
    data = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-data']

    def __str__(self):
        return f"Ajuste {self.medicao} - obra {self.obra.nome}"


class LancamentoManutencaoEquipamento(models.Model):
    ORIGEM_OBRA = 'OBRA'
    ORIGEM_ADMIN = 'ADMIN'
    ORIGEM_CHOICES = (
        (ORIGEM_OBRA, 'Obra'),
        (ORIGEM_ADMIN, 'Admin'),
    )

    medicao = models.ForeignKey(MedicaoEquipamento, on_delete=models.CASCADE, related_name='lancamentos_manutencao')
    dias = models.DecimalField(max_digits=5, decimal_places=2)
    origem = models.CharField(max_length=5, choices=ORIGEM_CHOICES)
    justificativa = models.TextField(blank=True, default="")
    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='lancamentos_manutencao_equipamento'
    )
    data_lancamento = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-data_lancamento']

    def __str__(self):
        return f"Manutenção {self.medicao} - {self.dias} dia(s)"


class LancamentoDisposicaoEquipamento(models.Model):
    ORIGEM_OBRA = 'OBRA'
    ORIGEM_ADMIN = 'ADMIN'
    ORIGEM_CHOICES = (
        (ORIGEM_OBRA, 'Obra'),
        (ORIGEM_ADMIN, 'Admin'),
    )

    medicao = models.ForeignKey(MedicaoEquipamento, on_delete=models.CASCADE, related_name='lancamentos_disposicao')
    dias = models.DecimalField(max_digits=5, decimal_places=2)
    origem = models.CharField(max_length=5, choices=ORIGEM_CHOICES)
    justificativa = models.TextField(blank=True, default="")
    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='lancamentos_disposicao_equipamento'
    )
    data_lancamento = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-data_lancamento']

    def __str__(self):
        return f"Disposição {self.medicao} - {self.dias} dia(s)"


class HistoricoMedicaoEquipamento(models.Model):
    """Log append-only de transições de status e alterações de valor. Nunca é
    editado nem apagado — só recebe novas linhas."""

    medicao = models.ForeignKey(MedicaoEquipamento, on_delete=models.CASCADE, related_name='historico')
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    data_hora = models.DateTimeField(auto_now_add=True)
    campo = models.CharField(max_length=50)
    valor_anterior = models.CharField(max_length=200, blank=True, default="")
    valor_novo = models.CharField(max_length=200, blank=True, default="")
    observacao = models.TextField(blank=True, default="")

    class Meta:
        ordering = ['-data_hora']
        verbose_name = 'Histórico de medição de equipamento'
        verbose_name_plural = 'Históricos de medição de equipamento'

    def __str__(self):
        return f"{self.medicao} - {self.campo} ({self.data_hora})"
