from django.db import models
from django.contrib.auth.models import AbstractUser


class Usuario(AbstractUser):
    qualificacao = [('o', 'obra'),
                    ('c', 'CEQ'),
                    ('a', 'Abastecedor (campo)')]

    status = models.CharField(max_length=1, choices=qualificacao, default='c')

    tanque_abastecimento = models.ForeignKey(
        'controleCEQ.Tanque', on_delete=models.PROTECT, null=True, blank=True,
        related_name='abastecedores', verbose_name='Tanque / comboio autorizado',
        help_text='Obrigatório para o perfil Abastecedor (campo).',
    )

    foto = models.ImageField(upload_to='fotos', blank=True, null=True)
    funcao = models.CharField(max_length=50, default="")

    perfis_estoque = [('solicitante', 'Solicitante'),
                       ('comprador', 'Comprador'),
                       ('almoxarifado', 'Almoxarifado')]

    perfil_estoque = models.CharField(max_length=20, choices=perfis_estoque, blank=True, default="")

    def __str__(self) -> str:
        return self.username

    def clean(self):
        super().clean()
        if self.status == 'a':
            from django.core.exceptions import ValidationError
            if not self.tanque_abastecimento_id:
                raise ValidationError({'tanque_abastecimento': 'Selecione o tanque ou comboio deste abastecedor.'})
            if self.is_superuser or self.is_staff:
                raise ValidationError({'status': 'O perfil de abastecedor não pode ter acesso administrativo.'})
