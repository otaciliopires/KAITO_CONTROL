# Generated by Django 4.1.5 on 2024-02-22 12:44

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('controleCEQ', '0004_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='abastecimento',
            name='colaborador',
        ),
        migrations.RemoveField(
            model_name='abastecimento',
            name='equipamento',
        ),
        migrations.RemoveField(
            model_name='abastecimento',
            name='obra',
        ),
        migrations.RemoveField(
            model_name='abastecimento',
            name='tanque',
        ),
        migrations.RemoveField(
            model_name='entrada',
            name='colaborador',
        ),
        migrations.RemoveField(
            model_name='entrada',
            name='obra',
        ),
        migrations.RemoveField(
            model_name='entrada',
            name='tanque',
        ),
        migrations.DeleteModel(
            name='Saldo',
        ),
        migrations.RemoveField(
            model_name='transferencia',
            name='colaborador',
        ),
        migrations.RemoveField(
            model_name='transferencia',
            name='fixo',
        ),
        migrations.RemoveField(
            model_name='transferencia',
            name='movel',
        ),
        migrations.DeleteModel(
            name='Abastecimento',
        ),
        migrations.DeleteModel(
            name='Entrada',
        ),
        migrations.DeleteModel(
            name='Tanque',
        ),
        migrations.DeleteModel(
            name='Transferencia',
        ),
    ]
