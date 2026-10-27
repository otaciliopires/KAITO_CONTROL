from django.db import models
from autenticacao.models import Usuario

class Equipamentos(models.Model):
    tipo_propriedade = (("R","ROCHA"),
                   ("T","TERCERIZADO"))
    unidades_medicao = (("H", "Horímetro"),
                    ("K", "Odômetro"))

    prefixo = models.CharField(max_length=20)
    descricao = models.CharField(max_length=50, null=True)
    tipo = models.CharField(max_length=5 ,choices=tipo_propriedade, default="ROCHA")
    proprietario = models.CharField(max_length=50, null=True)
    horímetro = models.FloatField(default=0)
    unidade_medicao = models.CharField(max_length=1, choices=unidades_medicao, default="H")
    elegivel_medicao = models.BooleanField(
        default=False,
        help_text="Marca se o equipamento participa da medição mensal (rateio de aluguel por obra).",
    )


    def __str__(self):
        return self.prefixo

class Obras(models.Model):
    nome = models.CharField(max_length=50)
    saldo = models.FloatField(default=0)
    tipo_status =  (("S","SALDO"),
                   ("M","MEDIÇÃO"),
                   ("E","ESTOQUE NA OBRA"))
    status = models.CharField(max_length=5, choices=tipo_status, default='S')
    usuario = models.ManyToManyField(Usuario) 
    endereço = models.CharField(max_length=100, default="" )   
    distancia = models.IntegerField(default=0)
    
    def __str__(self):
        return self.nome
    