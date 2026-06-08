from django.contrib.auth.models import AbstractUser
from django.db import models

class Role(models.Model):
    ADMIN = 'ADMIN'
    RRHH = 'RRHH'
    MEDICO = 'MEDICO'
    
    ROLE_CHOICES = [
        (ADMIN, 'Administrador'),
        (RRHH, 'Recursos Humanos'),
        (MEDICO, 'Médico / Personal'),
    ]
    
    name = models.CharField(max_length=50, choices=ROLE_CHOICES, unique=True)

    def __str__(self):
        return self.name

class CustomUser(AbstractUser):
    # Utilizamos el email como identificador principal en lugar de username
    email = models.EmailField(unique=True)
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True)
    failed_login_attempts = models.IntegerField(default=0)
    is_locked = models.BooleanField(default=False)
    locked_until = models.DateTimeField(null=True, blank=True)
    current_session_id = models.CharField(max_length=255, null=True, blank=True, verbose_name="ID de Sesión Actual")
    
    allow_otp_login = models.BooleanField(default=False)
    otp_code = models.CharField(max_length=6, null=True, blank=True)
    otp_created_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.email
