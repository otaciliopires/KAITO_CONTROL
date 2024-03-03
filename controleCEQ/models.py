from django.db import models
from autenticacao.models import Usuario
from datetime import date
from ativos.models import Obras, Equipamentos

# Create your models here.

class Tanque(models.Model):
    tipo_tanque = (("F","fixo"), 
                   ("M","movel"))

    prefixo = models.CharField(max_length=20)
    capacidade = models.IntegerField()
    estoque = models.FloatField()
    tipo = models.CharField(max_length=5 ,choices=tipo_tanque, default="fixo")
    descricao = models.TextField(default="")
    contador = models.FloatField(default=0)

    def __str__(self):
        return self.prefixo


class Entrada(models.Model):
    numero =models.IntegerField(default = 0)
    tanque = models.ForeignKey(Tanque, on_delete=models.DO_NOTHING)
    nota_fiscal = models.CharField(max_length=20)
    fornecedor = models.CharField(max_length=50)
    data_nf = models.DateField(default=date(2022,1,1))
    data_entrega = models.DateField(default=date(2022,1,1))
    obra = models.ForeignKey(Obras, on_delete=models.DO_NOTHING)
    quantidade = models.IntegerField(default=0)
    preco_unitario = models.FloatField()
    preco_total = models.FloatField()
    colaborador = models.ForeignKey(Usuario, on_delete=models.DO_NOTHING, null=True)
    descricao = models.TextField(default="")

    def __str__(self):
        return self.obra.nome

class Abastecimento(models.Model):
    numero = models.IntegerField(default = 0)
    litros = models.FloatField()
    contador_inicio = models.FloatField()
    contador_fim = models.FloatField()
    horimetro = models.FloatField()
    data = models.DateField()
    tanque = models.ForeignKey(Tanque, on_delete=models.DO_NOTHING)
    obra = models.ForeignKey(Obras, on_delete=models.DO_NOTHING, null=True)
    equipamento=models.ForeignKey(Equipamentos, on_delete=models.DO_NOTHING)
    lubrificacao = models.BooleanField(default=False)
    operador = models.CharField(max_length=50)
    colaborador = models.ForeignKey(Usuario, on_delete=models.DO_NOTHING)
    status = models.BooleanField(default=True)
    observacao = models.CharField(max_length=100, default="", null="")

    def __str__(self):
        return self.equipamento.prefixo


class Transferencia(models.Model):
    fixo = models.ForeignKey(Tanque, on_delete=models.DO_NOTHING, null=True, related_name='fixo_tanque')
    movel = models.ForeignKey(Tanque, on_delete=models.DO_NOTHING, null=True, related_name='movel_tanque')
    contador_inicio = models.FloatField()
    contador_fim = models.FloatField()
    litros = models.FloatField()
    contador_comboio = models.FloatField(default=0)
    colaborador = models.ForeignKey(Usuario, on_delete=models.DO_NOTHING)
    data = models.DateField(default='2022-01-01')

class Saldo(models.Model):
    ano = models.IntegerField(default=0)
    quantidade = models.FloatField()

    def __int__(self):
        return self.ano
