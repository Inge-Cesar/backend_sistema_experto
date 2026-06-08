from django.db import models
from modules.personal.models import Personal
from modules.base_conocimiento.models import Consultorio


class AsignacionTurno(models.Model):
    personal    = models.ForeignKey(
        Personal,
        on_delete=models.CASCADE,
        related_name='turnos',
        verbose_name="Profesional"
    )
    consultorio = models.ForeignKey(
        Consultorio,
        on_delete=models.CASCADE,
        related_name='turnos',
        verbose_name="Consultorio"
    )
    fecha       = models.DateField(verbose_name="Fecha")
    hora_inicio = models.TimeField(default='08:00', verbose_name="Hora de Inicio")
    hora_fin    = models.TimeField(default='16:00', verbose_name="Hora de Fin")
    creado_en   = models.DateTimeField(auto_now_add=True, verbose_name="Registrado el")

    class Meta:
        ordering = ['fecha', 'hora_inicio']
        verbose_name = "Asignación de Turno"
        verbose_name_plural = "Asignaciones de Turno"

    def __str__(self):
        return (
            f"{self.personal.nombres} {self.personal.apellidos} — "
            f"{self.fecha} ({self.hora_inicio}–{self.hora_fin})"
        )


# Alias de compatibilidad
ShiftAssignment = AsignacionTurno

class SolicitudCambioTurno(models.Model):
    ESTADOS = [
        ('Pendiente', 'Pendiente de Aceptación'),
        ('Aceptado', 'Aceptado por Colega (Esperando Admin)'),
        ('Aprobado_Admin', 'Aprobado por Administrador'),
        ('Rechazado', 'Rechazado / Vencido'),
    ]

    turno_original = models.ForeignKey(
        AsignacionTurno,
        on_delete=models.CASCADE,
        related_name='solicitudes_cambio',
        verbose_name="Turno Original"
    )
    medico_solicitante = models.ForeignKey(
        Personal,
        on_delete=models.CASCADE,
        related_name='cambios_solicitados',
        verbose_name="Médico Solicitante"
    )
    medico_reemplazante = models.ForeignKey(
        Personal,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cambios_aceptados',
        verbose_name="Médico Reemplazante (Aceptó el cambio)"
    )
    motivo = models.TextField(verbose_name="Motivo del Cambio")
    estado = models.CharField(max_length=20, choices=ESTADOS, default='Pendiente', verbose_name="Estado de la Solicitud")
    fecha_solicitud = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Solicitud")

    class Meta:
        ordering = ['-fecha_solicitud']
        verbose_name = "Solicitud de Cambio de Turno"
        verbose_name_plural = "Solicitudes de Cambio de Turno"

    def __str__(self):
        return f"Cambio de {self.medico_solicitante.nombres} para turno {self.turno_original.fecha} ({self.estado})"
