from django.db import models
from ativos.models import Equipamentos, Obras

# Create your models here.


class Ordem_Oficina(models.Model):
    equipamento = models.ForeignKey(Equipamentos, on_delete=models.DO_NOTHING)
    data_inicio = models.DateTimeField()
    data_fim = models.DateTimeField(null=True, blank=True)
    data_status = models.DateTimeField(null=True, blank=True)
    tempo_aguardo_peca = models.FloatField(null=True, blank=True, default=0.0)
    tempo_aguardo_servico = models.FloatField(null=True, blank=True, default=0.0)
    tempo_em_servico = models.FloatField(null=True, blank=True, default=0.0)
    tempo_total = models.FloatField(default=0.0)
    tipo_status = (("AP", "Aguardando Peças"), ("AS", "Aguardando Serviço"), ("ES", "Em Serviço"))
    status = models.CharField(max_length=5, choices = tipo_status, default="Aguardando Serviço")
    numero = models.IntegerField()
    horimetro = models.FloatField()
    data_status = models.DateTimeField(null=True, blank=True)

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

    def __str__(self):
        return self.nome

    
class Grupo_Servico(models.Model):

    grupo = models.CharField(max_length=50)

    def __str__(self):
        return self.grupo


class Servico_Oficina(models.Model):
    numero = models.IntegerField() 
    ordem_servico = models.ForeignKey(Ordem_Oficina, on_delete=models.DO_NOTHING)
    tipo_status = (("AP", "Aguardando Peças"), ("AS", "Aguardando Serviço"), ("ES", "Em Serviço"))
    status = models.CharField(max_length=5, choices = tipo_status, default="Em Serviço")
    grupo_servico = models.ForeignKey(Grupo_Servico, on_delete=models.DO_NOTHING)
    descricao = models.CharField(max_length = 100)
    tempo_aguardo_peca = models.FloatField(null=True, blank=True, default=0)
    tempo_aguardo_servico = models.FloatField(null=True, blank=True, default=0)
    tempo_em_servico = models.FloatField(null=True, blank=True, default=0)
    tempo_total = models.FloatField(null=True, blank=True, default=0)
    data_inicio = models.DateTimeField()
    data_mudanca_status = models.DateTimeField(null=True, blank=True)
    data_fim = models.DateTimeField(null=True, blank=True)
    tipo_executante = (("F", "Funcionario"),("T", "Terceirizado"))
    executante = models.CharField(max_length=50, choices=tipo_executante, default="Funcionario")
    executante_terceiro = models.ForeignKey(Servico_Terceirizado, null=True, blank=True, on_delete=models.DO_NOTHING)
    executante_funcionario = models.ForeignKey(Funcionario, null=True, blank=True, on_delete=models.DO_NOTHING)

    def __str__(self):
        return self.grupo_servico.grupo


class Solicitacao(models.Model):
    insumo = models.CharField(max_length=200)
    equipamento = models.ForeignKey(Equipamentos, on_delete=models.DO_NOTHING)
    comprador = models.ForeignKey(Funcionario,  on_delete=models.DO_NOTHING)
    solicitacao = models.IntegerField()
    data_suprimentos = models.DateTimeField()
    tipo_status = (("BP", "Baixa Prioridade"), ("MP", "Média Prioridade"), ("AP", "Alta Prioridade"), ("UR", "Urgente"))
    status = models.CharField(max_length=50,choices = tipo_status, default="Baixa Prioridade")
    data_previsao = models.DateField(null=True, blank=True)
    link_solicitacao= models.CharField(max_length=500, blank=True)
    observacao = models.CharField(max_length=1000, blank=True)
    atendida = models.BooleanField(default=False)

    def __str__(self):
        return self.insumo

class Socorro(models.Model):
    numero = models.IntegerField()
    obra = models.ForeignKey(Obras, on_delete=models.DO_NOTHING)
    data_saida = models.DateTimeField()
    data_chegada = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.obra.nome
    
class Servico_Socorro(models.Model):
    equipamento = models.ForeignKey(Equipamentos, on_delete=models.DO_NOTHING)
    numero = models.IntegerField(default=0)
    socorro = models.ForeignKey(Socorro, on_delete=models.DO_NOTHING)
    grupo_servico = models.ForeignKey(Grupo_Servico, on_delete=models.DO_NOTHING)
    mecanico = models.ForeignKey(Funcionario, on_delete=models.DO_NOTHING)
    data_inicio = models.DateTimeField(null=True, blank=True)
    data_fim = models.DateTimeField(null=True, blank=True)
    tempo_servico = models.FloatField(default=0.0)
    descricao = models.CharField(max_length=500)
    resultado_servico = models.BooleanField(default=False)

    def __str__(self):
        return self.equipamento.prefixo

class Servico_Preventiva(models.Model):
    descricao = models.CharField(max_length=500)
    insumo = models.CharField(max_length=100)
    quantidade = models.FloatField(null=True, blank=True)

    def __str__(self):
        return self.descricao
    


class Ordem_Preventiva(models.Model):
    periodo = models.IntegerField()
    servicos = models.ManyToManyField(Servico_Preventiva)
    equipamento = models.ForeignKey(Equipamentos, on_delete=models.DO_NOTHING )
    
    def __str__(self):
        return f'{self.equipamento.prefixo} - {self.periodo}'

class Preventiva(models.Model):
    ordem = models.ForeignKey(Ordem_Preventiva,on_delete=models.DO_NOTHING)
    horimetro = models.FloatField(null=True, blank=True)
    data_emissao = models.DateField()
    data_insumo= models.DateField(null=True, blank=True)
    local = models.ForeignKey(Obras, on_delete=models.DO_NOTHING)
    data_inicio = models.DateTimeField(null=True, blank=True)
    data_fim = models.DateTimeField(null=True, blank=True)
    tempo_servico = models.FloatField(default=0.0)
    assinatura_responsavel = models.BooleanField(default=False)
    numero = models.IntegerField()
    mecanico = models.ForeignKey(Funcionario, on_delete=models.DO_NOTHING,null=True)

    def __str__(self):
        return self.ordem.equipamento.prefixo



class Registro_Tempo_Servico(models.Model):
    servico_oficina = models.ForeignKey(Servico_Oficina, on_delete=models.DO_NOTHING, blank=True, null=True)
    servico_socorro = models.ForeignKey(Servico_Socorro, on_delete=models.DO_NOTHING, blank=True, null=True)
    servico_preventiva = models.ForeignKey(Servico_Preventiva, on_delete=models.DO_NOTHING, blank=True, null=True)
    funcionario = models.ForeignKey(Funcionario, on_delete=models.DO_NOTHING, null=True, blank=True)
    tercerizado = models.ForeignKey(Servico_Terceirizado, on_delete=models.DO_NOTHING, null=True, blank=True)
    data_inicial = models.DateTimeField(null=True, blank=True)
    data_final = models.DateTimeField(null=True, blank=True)
    tempo_servico = models.FloatField(null=True, blank=True)
    descricao = models.CharField(max_length=500, default="")
    
    def __str__(self):
        return self.funcionario.nome

    


    