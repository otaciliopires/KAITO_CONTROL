from django.contrib import admin
from .models import Obras, Equipamentos

# Register your models here.
admin.site.register(Obras)


class EquipamentosAdmin(admin.ModelAdmin):
    list_filter = ('prefixo', 'proprietario')

admin.site.register(Equipamentos, EquipamentosAdmin)