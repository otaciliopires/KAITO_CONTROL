from django.db import models
from ativos.models import Equipamentos, Obras

# Create your models here.


class Ordem_Oficina(models.Model):
    equipamento = models.ForeignKey(Equipamentos, on_delete=models.DO_NOTHING)
    data_inicio = models.DateTimeField()
    data_fim = models.DateTimeField(null=True, blank=True)
    tempo_aguardo_peca = models.FloatField(null=True, blank=True)
    tempo_aguardo_servico = models.FloatField(null=True, blank=True)
    tempo_em_servico = models.FloatField(null=True, blank=True)
    tempo_total = models.FloatField(null=True, blank=True)
    tipo_status = (("AP", "Aguardando Peças"), ("AS", "Aguardando Serviço"), ("ES", "Em Serviço"))
    status = models.CharField(max_length=5, choices = tipo_status, default="Aguardando Serviço")
    numero = models.IntegerField()
    horimetro = models.FloatField()

    def __str__(self):
        return self.equipamento.prefixo
    
class Funcionario(models.Model):

    nome = models.CharField(max_length=50)
    funcao = models.CharField(max_length=50)

    def __str__(self):
        return self.nome


class Servico_Terceirizado(models.Model):

    nome = models.CharField(max_length=50)
    descricao = models.CharField(max_length=50)

    
class Grupo_Servico(models.Model):

    grupo = models.CharField(max_length=50)

    def __str__(self):
        return self.grupo


class Servico_Oficina(models.Model):
    numero = models.IntegerField() 
    ordem_servico = models.ForeignKey(Ordem_Oficina, on_delete=models.DO_NOTHING)
    tipo_status = (("AP", "Aguardando Peças"), ("AS", "Aguardando Serviço"), ("ES", "Em Serviço"))
    status = models.CharField(max_length=5, choices = tipo_status, default="Aguardando Peças")
    grupo_servico = models.ForeignKey(Grupo_Servico, on_delete=models.DO_NOTHING)
    descricao = models.CharField(max_length = 100)
    data_inicio = models.DateTimeField()
    data_fim = models.DateTimeField(null=True)
    executante_terceiro = models.ForeignKey(Servico_Terceirizado, null=True, blank=True, on_delete=models.DO_NOTHING)
    executante_funcionario = models.ForeignKey(Funcionario, null=True, blank=True, on_delete=models.DO_NOTHING)

    def __str__(self):
        return self.grupo_servico.grupo

    


    