from django.conf import settings
from django.db import models

from ativos.models import Obras
from controleCEQ.models import Tanque


class CaminhaoAbastecedor(models.Model):
    tanque = models.OneToOneField(
        Tanque, on_delete=models.PROTECT,
        limit_choices_to={'tipo': 'M'},
        related_name='caminhao_abastecedor',
    )
    identificacao = models.CharField(max_length=30)
    marca = models.CharField(max_length=50, blank=True, default="")
    descricao_locacao = models.TextField(
        default=(
            "Locação de CAMINHÃO DE ABASTECIMENTO, combustível diesel, "
            "sem operador, sendo o fornecimento de combustível por conta "
            "da LOCATÁRIA;"
        )
    )
    ativo = models.BooleanField(default=True)

    def __str__(self):
        return self.identificacao


class ValorMensalCaminhao(models.Model):
    caminhao = models.ForeignKey(CaminhaoAbastecedor, on_delete=models.CASCADE, related_name='valores_mensais')
    valor = models.FloatField()
    vigente_desde = models.DateField()

    class Meta:
        ordering = ['-vigente_desde']

    def __str__(self):
        return f"{self.caminhao} - R$ {self.valor} desde {self.vigente_desde}"


class ParametroTaxaDiesel(models.Model):
    percentual = models.FloatField(help_text="Ex: 5 para 5%")
    vigente_desde = models.DateField()

    class Meta:
        ordering = ['-vigente_desde']

    def __str__(self):
        return f"{self.percentual}% desde {self.vigente_desde}"


class ContratoMedicaoCaminhao(models.Model):
    obra = models.ForeignKey(Obras, on_delete=models.CASCADE, related_name='contratos_medicao_caminhao')
    caminhao = models.ForeignKey(CaminhaoAbastecedor, on_delete=models.PROTECT, related_name='contratos')
    ativo = models.BooleanField(default=True)

    mes_referencia_inicial = models.DateField(
        help_text="Primeiro mês (dia 1) controlado pelo Kaito. Meses anteriores não aparecem na grade de medição."
    )
    numero_anterior = models.IntegerField(
        default=0,
        help_text="Número da última medição fechada (do boletim físico mais recente). A próxima medição gerada será este número + 1 — atualize aqui sempre que fechar uma medição.",
    )

    quantidade_anterior_locacao = models.FloatField(
        default=0, help_text="Quantidade (em meses) acumulada até a última medição fechada."
    )
    valor_anterior_locacao = models.FloatField(
        default=0, help_text="Valor (R$) de locação acumulado até a última medição fechada."
    )
    quantidade_anterior_diesel = models.FloatField(
        default=0, help_text="Litros de diesel acumulados até a última medição fechada."
    )
    valor_anterior_diesel = models.FloatField(
        default=0, help_text="Valor (R$) da taxa de diesel acumulado até a última medição fechada."
    )

    class Meta:
        unique_together = ('obra', 'caminhao')

    def __str__(self):
        return f"{self.obra.nome} - {self.caminhao.identificacao}"


class FechamentoMedicaoCaminhao(models.Model):
    contrato = models.ForeignKey(ContratoMedicaoCaminhao, on_delete=models.CASCADE, related_name='fechamentos')
    ano = models.IntegerField()
    mes = models.IntegerField()
    fechado_em = models.DateTimeField(auto_now_add=True)
    fechado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        unique_together = ('contrato', 'ano', 'mes')

    def __str__(self):
        return f"{self.contrato} - {self.mes:02d}/{self.ano}"
