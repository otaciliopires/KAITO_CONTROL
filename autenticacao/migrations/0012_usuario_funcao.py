# Generated by Django 4.1.5 on 2024-01-28 23:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('autenticacao', '0011_alter_usuario_foto'),
    ]

    operations = [
        migrations.AddField(
            model_name='usuario',
            name='funcao',
            field=models.CharField(default='', max_length=50),
        ),
    ]
