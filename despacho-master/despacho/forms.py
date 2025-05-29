# Python
from django import forms
from .models import Cliente, Caso, Perfil
from django.contrib.auth.models import User

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nombre', 'telefono', 'email']
        widgets = {
            'nombre': forms.TextInput(attrs={'required': True}),
            'telefono': forms.TextInput(attrs={'required': True}),
            'email': forms.EmailInput(attrs={'required': True}),
        }


class CasoForm(forms.ModelForm):
    class Meta:
        model = Caso
        fields = ['cliente', 'titulo', 'descripcion', 'estado', 'fecha_inicio', 'fecha_fin', 'asignado_a']
        widgets = {
            'cliente': forms.Select(attrs={'required': True}),
            'titulo': forms.TextInput(attrs={'required': True}),
            'descripcion': forms.Textarea(attrs={'required': False}),
            'estado': forms.Select(attrs={'required': True}),
            'fecha_inicio': forms.DateInput(attrs={'type': 'date', 'required': True}),
            'fecha_fin': forms.DateInput(attrs={'type': 'date', 'required': False}),
            'asignado_a': forms.Select(attrs={'required': False}),
        }

class UserForm(forms.ModelForm):
    rol = forms.ChoiceField(choices=Perfil.ROL_CHOICES, required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password', 'rol']
        widgets = {
            'username': forms.TextInput(attrs={'required': True}),
            'email': forms.EmailInput(attrs={'required': True}),
            'first_name': forms.TextInput(attrs={'required': True}),
            'last_name': forms.TextInput(attrs={'required': True}),
            'password': forms.PasswordInput(attrs={'required': True}),
        }


