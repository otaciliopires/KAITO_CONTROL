from django.db import models
from django.contrib.auth.models import AbstractUser
# Create your models here.


class Usuario(AbstractUser):
    qualificacao = [('o', 'obra'),
                    ('c', 'CEQ')]

    status = models.CharField(max_length=1, choices=qualificacao, default='c')


    foto = models.ImageField(upload_to='fotos')
    funcao = models.CharField(max_length=50, default="")
    def __str__(self) -> str:
        return self.username

 