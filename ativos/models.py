from django.db import models
from autenticacao.models import Usuario




class Equipamentos(models.Model):
    prefixo = models.CharField(max_length=20)
    descricao = models.CharField(max_length=50, null=True)
    tipo_propriedade = (("R","ROCHA"), 
                   ("T","TERCERIZADO"))
    tipo = models.CharField(max_length=5 ,choices=tipo_propriedade, default="ROCHA")
    proprietario = models.CharField(max_length=50, null=True)
    horímetro = models.FloatField(default=0)



    def __str__(self):
        return self.prefixo


class Obras(models.Model):
    nome = models.CharField(max_length=50)
    saldo = models.FloatField(default=0)
    usuario = models.ManyToManyField(Usuario) 
    endereço = models.CharField(max_length=100, default="" )   
    distancia = models.IntegerField(default=0)
    
    def __str__(self):
        return self.nome
    