from django.contrib import admin
from .models import Tanque, Abastecimento, Entrada, Transferencia, Saldo

# Register your models here.




admin.site.register(Tanque)


@admin.register(Abastecimento)
class AbastecimentoAdmin(admin.ModelAdmin):
    list_display=('equipamento','obra', 'litros', 'data', )
admin.site.register(Transferencia)
admin.site.register(Entrada)
admin.site.register(Saldo)
