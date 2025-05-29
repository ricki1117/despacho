from django.db import models
from django.contrib.auth.models import User


class Cliente(models.Model):
    nombre = models.CharField(max_length=100)
    telefono = models.CharField(max_length=20)
    email = models.EmailField(unique=True)
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='clientes')

    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'

    def __str__(self):
        return self.nombre


class Caso(models.Model):
    ESTADO_CHOICES = [
        ('Abierto', 'Abierto'),
        ('Cerrado', 'Cerrado'),
        ('En Proceso', 'En Proceso'),
    ]

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='casos')
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='Abierto')
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField(null=True, blank=True)
    asignado_a = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='casos_asignados')

    class Meta:
        verbose_name = 'Caso'
        verbose_name_plural = 'Casos'

    def __str__(self):
        return self.titulo


# This model extends the User model if you want to add role information
class Perfil(models.Model):
    ROL_CHOICES = [
        ('admin', 'Administrador'),
        ('abogado', 'Abogado'),
    ]

    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    rol = models.CharField(max_length=10, choices=ROL_CHOICES, default='abogado')

    class Meta:
        verbose_name = 'Perfil'
        verbose_name_plural = 'Perfiles'

    def __str__(self):
        return f"{self.usuario.username} - {self.get_rol_display()}"