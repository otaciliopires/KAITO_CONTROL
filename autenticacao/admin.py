from django.contrib import admin
from autenticacao.models import Usuario
from .forms import UserChangeForm, UserCreationForm
from django.contrib.auth import admin as admin_auth_django

# Register your models here.
@admin.register(Usuario)
class UsuarioAdmin(admin_auth_django.UserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    model = Usuario
    list_display = ("id", "username", "email", "first_name", "last_name", "is_staff", "status", 'foto')
 
    fieldsets = admin_auth_django.UserAdmin.fieldsets + (('Qualificação', {"fields": ("status","funcao")}), ('Imagem', {"fields": ("foto",)}))