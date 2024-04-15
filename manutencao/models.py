from django.db import models
from ativos.models import Equipamentos, Obras

# Create your models here.


class Ordem_Oficina(models.Model):
    equipamento = models.ForeignKey(Equipamentos, on_delete=models.DO_NOTHING)
    data_inicio = models.DateField()
    data_fim = models.DateField()
    tempo_aguardo_peca = models.FloatField()
    tempo_aguardo_servico = models.FloatField()
    tempo_em_servico = models.FloatField()
    tipo_status = (("AP", "Aguardando Peças"), ("AS", "Aguardando Serviço"), ("ES", "Em Serviço"))
    status = models.CharField(max_length=5, choices = tipo_status, default="Aguardando Peças")
    numero = models.IntegerField()
    horimetro = models.FloatField()



def __str__(self):
        return self.equipamento
    
# class Funcionario(models.Model):

#     nome = models.CharField(max_length=50)
#     funcao = models.CharField(max_length=50)

#     def __str__(self):
#         return self.nome


# class Servico_Terceirizado(models.Model):

#     nome = models.CharField(max_length=50)
#     descricao = models.CharField(max_length=50)

    
# class Grupo_Servico(models.Model):

#     grupo = models.ChardField(max_length=50)

#     def __str__(self):
#         return self.tipo


# class Servico_Oficina(models.Model):
#     numero = models.IntegerField() 
#     ordem_servico = models.ForeignKey(Ordem_Oficina)
#     tipo_status = (("AP", "Aguardando Peças"), ("AS", "Aguardando Serviço"), ("ES", "Em Serviço"))
#     status = models.CharField(max_length=5, choices = tipo_status, default="Aguardando Peças")
#     grupo_servico = models.ForeignKey(Grupo_Servico)
#     descricao = models.CharField(max_length = 100)
#     data_inicio = models.DateField()
#     data_fim = models.DateField()
#     executante_terceiro = models.ForeignKey(Servico_Terceirizado, null=True)
#     executante_funcionario = models.ForeignKey(Funcionario, null=True)

#     def __str__(self):
#         return self.tipo_servico

    


    