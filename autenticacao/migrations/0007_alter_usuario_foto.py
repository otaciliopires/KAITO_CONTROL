# Generated by Django 4.1.5 on 2024-01-28 22:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('autenticacao', '0006_alter_usuario_foto'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usuario',
            name='foto',
            field=models.ImageField(blank=True, default='media/fotos/otacilio.png', null=True, upload_to='fotos/'),
        ),
    ]
