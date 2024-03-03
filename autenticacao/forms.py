from django.contrib.auth import forms
from .models import Usuario



class UserChangeForm(forms.UserChangeForm):
    class Meta(forms.UserChangeForm.Meta):
        model = Usuario #classe criada no seu models.py

class UserCreationForm(forms.UserCreationForm):
    class Meta(forms.UserChangeForm.Meta):
        model = Usuario
