from django.db import models
from django.conf import settings

class RegistroAuditoria(models.Model):
    NIVEL_CHOICES = (
        ('INFO', 'Informativo'),
        ('ADVERTENCIA', 'Advertencia'),
        ('CRITICO', 'Crítico'),
    )

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name="Usuario / Sistema",
        help_text="Usuario que realizó la acción. Nulo si fue un proceso automático del sistema."
    )
    accion = models.CharField(max_length=100, verbose_name="Acción Realizada")
    detalles = models.TextField(verbose_name="Detalles de la Acción")
    nivel_severidad = models.CharField(max_length=20, choices=NIVEL_CHOICES, default='INFO', verbose_name="Severidad")
    motivo = models.TextField(null=True, blank=True, verbose_name="Motivo de la Acción", help_text="Justificación si es una acción manual forzada.")
    fecha = models.DateTimeField(auto_now_add=True, verbose_name="Fecha y Hora")

    class Meta:
        verbose_name = "Registro de Auditoría"
        verbose_name_plural = "Registros de Auditoría"
        ordering = ['-fecha']

    def __str__(self):
        return f"[{self.nivel_severidad}] {self.accion} - {self.fecha.strftime('%Y-%m-%d %H:%M:%S')}"

class BlacklistedIP(models.Model):
    ip_address = models.GenericIPAddressField(unique=True, verbose_name="Dirección IP")
    reason = models.CharField(max_length=255, default="Acceso a Honeypot", verbose_name="Motivo del Bloqueo")
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "IP en Lista Negra"
        verbose_name_plural = "IPs en Lista Negra"

    def __str__(self):
        return f"{self.ip_address} - {self.reason}"
