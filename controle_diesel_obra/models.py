from django.conf import settings
from django.db import models

from ativos.models import Obras


class TanqueObra(models.Model):
    obra = models.OneToOneField(Obras, on_delete=models.PROTECT, related_name='tanque_diesel')
    capacidade = models.FloatField(default=0)
    estoque = models.FloatField(default=0)
    descricao = models.TextField(blank=True, default="")

    def __str__(self):
        return f"Tanque - {self.obra.nome}"


class EquipamentoObra(models.Model):
    tipo_propriedade = (
        ("R", "ROCHA"),
        ("T", "TERCEIRIZADO"),
    )
    unidades_medicao = (
        ("KM", "Quilometragem"),
        ("H", "Horímetro"),
    )

    obra = models.ForeignKey(Obras, on_delete=models.CASCADE, related_name='equipamentos_diesel')
    prefixo = models.CharField(max_length=30)
    descricao = models.CharField(max_length=100, blank=True, default="")
    tipo = models.CharField(max_length=5, choices=tipo_propriedade, default="R")
    unidade_medicao = models.CharField(max_length=5, choices=unidades_medicao, default="H")
    contador_atual = models.FloatField(default=0)
    ativo = models.BooleanField(default=True)

    class Meta:
        unique_together = ('obra', 'prefixo')

    def __str__(self):
        return self.prefixo


class EntradaDiesel(models.Model):
    obra = models.ForeignKey(Obras, on_delete=models.PROTECT, related_name='entradas_diesel')
    numero = models.IntegerField(default=0)
    nota_fiscal = models.CharField(max_length=20)
    fornecedor = models.CharField(max_length=50)
    data_nf = models.DateField()
    data_entrega = models.DateField()
    quantidade = models.FloatField()
    preco_unitario = models.FloatField()
    preco_total = models.FloatField()
    colaborador = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    descricao = models.TextField(blank=True, default="")

    class Meta:
        ordering = ['-numero']

    def __str__(self):
        return f"Entrada #{self.numero} - {self.obra.nome}"


class SaidaDiesel(models.Model):
    obra = models.ForeignKey(Obras, on_delete=models.PROTECT, related_name='saidas_diesel')
    numero = models.IntegerField(default=0)
    equipamento = models.ForeignKey(EquipamentoObra, on_delete=models.PROTECT, related_name='saidas')
    litros = models.FloatField()
    contador_inicio = models.FloatField()
    contador_fim = models.FloatField()
    data = models.DateField()
    operador = models.CharField(max_length=50)
    colaborador = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    observacao = models.CharField(max_length=200, blank=True, default="")

    class Meta:
        ordering = ['-numero']

    def __str__(self):
        return f"Saída #{self.numero} - {self.equipamento.prefixo}"
