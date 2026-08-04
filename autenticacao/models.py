from django.db import models
from django.contrib.auth.models import AbstractUser
# Create your models here.


class Usuario(AbstractUser):
    qualificacao = [('o', 'obra'),
                    ('c', 'CEQ')]

    status = models.CharField(max_length=1, choices=qualificacao, default='c')


    foto = models.ImageField(upload_to='fotos', blank=True, null=True)
    funcao = models.CharField(max_length=50, default="")

    perfis_estoque = [('solicitante', 'Solicitante'),
                       ('comprador', 'Comprador'),
                       ('almoxarifado', 'Almoxarifado')]

    perfil_estoque = models.CharField(max_length=20, choices=perfis_estoque, blank=True, default="")

    def __str__(self) -> str:
        return self.username

 