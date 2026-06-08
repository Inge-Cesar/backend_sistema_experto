from django.db import models
from django.conf import settings
from cryptography.fernet import Fernet, MultiFernet
import base64

def get_fernet():
    # Llave nueva exclusiva (Segregación criptográfica)
    new_key_str = getattr(settings, 'PERSONAL_ENCRYPTION_KEY', getattr(settings, 'SECRET_KEY', 'x'*32))[:32].encode()
    new_key = new_key_str.ljust(32, b'X')[:32]
    f_new = Fernet(base64.urlsafe_b64encode(new_key))
    
    # Llave antigua (Para desencriptar registros viejos sin romper la base de datos)
    old_key_str = getattr(settings, 'SECRET_KEY', 'x'*32)[:32].encode()
    old_key = old_key_str.ljust(32, b'X')[:32]
    f_old = Fernet(base64.urlsafe_b64encode(old_key))
    
    # MultiFernet usa f_new para encriptar, y prueba f_new luego f_old para desencriptar
    return MultiFernet([f_new, f_old])

class EncryptedCharField(models.CharField):
    description = "Campo con cifrado AES mediante Fernet"

    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        try:
            return get_fernet().decrypt(value.encode()).decode()
        except Exception:
            return value

    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        if value is None or value == '':
            return value
        if value.startswith('gAAAAA'):
            return value
        return get_fernet().encrypt(str(value).encode()).decode()


class EncryptedTextField(models.TextField):
    description = "Campo de texto con cifrado AES mediante Fernet"

    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        try:
            return get_fernet().decrypt(value.encode()).decode()
        except Exception:
            return value

    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        if value is None or value == '':
            return value
        if value.startswith('gAAAAA'):
            return value
        return get_fernet().encrypt(str(value).encode()).decode()


class Personal(models.Model):
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='perfil_personal',
        verbose_name="Usuario del Sistema"
    )

    # Datos encriptados con AES (Fernet)
    nombres    = EncryptedCharField(max_length=255, verbose_name="Nombres")
    apellidos  = EncryptedCharField(max_length=255, verbose_name="Apellidos")
    cedula     = EncryptedCharField(max_length=255, unique=True, verbose_name="Cédula de Identidad")
    correo     = EncryptedCharField(max_length=255, blank=True, null=True, verbose_name="Correo Electrónico")
    direccion  = EncryptedTextField(blank=True, null=True, verbose_name="Dirección")

    # Datos operativos
    especialidad        = models.CharField(max_length=100, verbose_name="Especialidad Médica")
    horas_max_semanales = models.IntegerField(default=48, verbose_name="Límite Semanal (horas)")
    apto_nocturno       = models.BooleanField(
        default=True,
        verbose_name="Apto para Turnos Nocturnos",
        help_text="Indica si el profesional tiene aptitud médica para trabajar en horario nocturno"
    )
    foto = models.ImageField(
        upload_to='fotos_personal/',
        null=True, blank=True,
        verbose_name="Fotografía de Perfil"
    )

    creado_en = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Registro")

    # Nuevos campos exigidos por el Motor Experto
    CATEGORIAS = [
        ('Especialista', 'Médico Especialista'),
        ('General', 'Médico General'),
        ('Enfermera', 'Enfermera Licenciada'),
        ('Tecnico', 'Técnico / Paramédico'),
        ('Auxiliar', 'Auxiliar de Enfermería'),
    ]
    categoria = models.CharField(max_length=50, choices=CATEGORIAS, default='Especialista', verbose_name="Categoría Profesional")
    
    haber_basico = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Haber Básico (Salario)")
    
    SERVICIOS = [
        ('Emergencias', 'Emergencias / Urgencias'),
        ('UCI', 'Unidad de Cuidados Intensivos (UCI)'),
        ('Hospitalizacion', 'Hospitalización (Planta)'),
        ('Consulta', 'Consulta Externa'),
        ('Quirofano', 'Quirófano / Cirugía'),
        ('Laboratorio', 'Laboratorio / Imagenología'),
    ]
    servicio_asignado = models.CharField(max_length=50, choices=SERVICIOS, default='Consulta', verbose_name="Servicio Asignado")
    
    sala_habitual = models.CharField(max_length=100, blank=True, null=True, verbose_name="Sala / Consultorio Habitual")
    antiguedad_meses = models.IntegerField(default=0, verbose_name="Antigüedad (meses)")
    
    voluntario_feriados = models.BooleanField(default=False, verbose_name="Voluntario para Feriados")
    
    en_vacaciones = models.BooleanField(default=False, verbose_name="En Vacaciones")
    fecha_fin_vacaciones = models.DateField(blank=True, null=True, verbose_name="Fecha Fin de Vacaciones")
    
    permiso_activo = models.BooleanField(default=False, verbose_name="Permiso Activo")
    fecha_fin_permiso = models.DateField(blank=True, null=True, verbose_name="Fecha Fin de Permiso")

    class Meta:
        verbose_name = "Personal Médico"
        verbose_name_plural = "Personal Médico"
        ordering = ['-creado_en']

    def __str__(self):
        return f"{self.nombres} {self.apellidos} ({self.especialidad})"


class SolicitudPermiso(models.Model):
    TIPOS = [
        ('Vacaciones', 'Vacaciones Anuales'),
        ('Enfermedad', 'Baja por Enfermedad'),
        ('Maternidad_Paternidad', 'Licencia Maternidad/Paternidad'),
        ('Luto', 'Licencia por Luto'),
        ('Especial', 'Permiso Especial'),
    ]
    ESTADOS = [
        ('Pendiente', 'Pendiente de Aprobación'),
        ('Aprobado', 'Aprobado'),
        ('Rechazado', 'Rechazado'),
    ]

    personal = models.ForeignKey(
        Personal, 
        on_delete=models.CASCADE, 
        related_name='solicitudes_permiso',
        verbose_name="Personal Médico"
    )
    tipo = models.CharField(max_length=50, choices=TIPOS, verbose_name="Tipo de Permiso")
    fecha_inicio = models.DateField(verbose_name="Fecha de Inicio")
    fecha_fin = models.DateField(verbose_name="Fecha de Fin")
    motivo = models.TextField(verbose_name="Motivo o Justificación")
    estado = models.CharField(max_length=20, choices=ESTADOS, default='Pendiente', verbose_name="Estado de Solicitud")
    fecha_solicitud = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Solicitud")

    class Meta:
        verbose_name = "Solicitud de Permiso"
        verbose_name_plural = "Solicitudes de Permisos"
        ordering = ['-fecha_solicitud']

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.personal.nombres} ({self.estado})"


# Alias para compatibilidad con código antiguo durante la transición
Personnel = Personal
