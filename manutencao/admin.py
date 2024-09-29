from django.contrib import admin
from.models import Ordem_Oficina, Servico_Oficina, Grupo_Servico, Funcionario, Servico_Terceirizado, Solicitacao, Socorro, Servico_Socorro

# Register your models here.


admin.site.register(Ordem_Oficina)
admin.site.register(Servico_Oficina)
admin.site.register(Grupo_Servico)
admin.site.register(Funcionario)
admin.site.register(Servico_Terceirizado)
admin.site.register(Solicitacao)
admin.site.register(Socorro)
@admin.register(Servico_Socorro)
class Servico_SocorroAdmin(admin.ModelAdmin):
    list_display=('equipamento','data_inicio', 'data_fim', 'mecanico','tempo_servico', 'resultado_servico')
