from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('controleCEQ', '0010_reciboabastecimentocampo')]
    operations = [migrations.AddField(model_name='abastecimento', name='assinatura', field=models.JSONField(blank=True, default=dict, verbose_name='Assinatura do motorista / operador'))]
