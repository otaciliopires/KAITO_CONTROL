# Generated by Django 4.1.5 on 2024-04-16 17:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manutencao', '0005_alter_ordem_oficina_data_fim_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='ordem_oficina',
            name='tempo_total',
            field=models.FloatField(blank=True, null=True),
        ),
    ]
