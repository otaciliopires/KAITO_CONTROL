from django.contrib import admin
from.models import Ordem_Oficina, Servico_Oficina, Grupo_Servico, Funcionario

# Register your models here.


admin.site.register(Ordem_Oficina)
admin.site.register(Servico_Oficina)
admin.site.register(Grupo_Servico)
admin.site.register(Funcionario)