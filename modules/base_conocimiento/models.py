from django.db import models


class Hecho(models.Model):
    clave       = models.CharField(max_length=100, unique=True, verbose_name="Clave", help_text="Ejemplo: HORAS_DESCANSO_MIN")
    valor       = models.JSONField(verbose_name="Valor", help_text="Valor del hecho (int, string, lista, diccionario)")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")

    class Meta:
        verbose_name = "Hecho"
        verbose_name_plural = "Hechos"

    def __str__(self):
        return f"{self.clave}: {self.valor}"


class Regla(models.Model):
    nombre      = models.CharField(max_length=100, unique=True, verbose_name="Nombre")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")
    condicion   = models.JSONField(verbose_name="Condición", help_text="Estructura lógica en formato JSON")
    accion      = models.JSONField(verbose_name="Acción", help_text="Acción a ejecutar en formato JSON")
    prioridad   = models.IntegerField(default=10, verbose_name="Prioridad", help_text="Mayor prioridad se evalúa primero")
    activo      = models.BooleanField(default=True, verbose_name="Activa")

    class Meta:
        ordering = ['-prioridad']
        verbose_name = "Regla"
        verbose_name_plural = "Reglas"

    def __str__(self):
        return self.nombre


class ServicioMedico(models.Model):
    nombre                = models.CharField(max_length=100, unique=True, verbose_name="Nombre", help_text="Ej: Urgencias, Pediatría, UCI")
    descripcion           = models.TextField(blank=True, null=True, verbose_name="Descripción")
    activo                = models.BooleanField(default=True, verbose_name="Activo")
    capacidad_concurrente = models.IntegerField(default=1, verbose_name="Capacidad Concurrente", help_text="Máx. de médicos simultáneos en este servicio")

    class Meta:
        verbose_name = "Servicio Médico"
        verbose_name_plural = "Servicios Médicos"

    def __str__(self):
        return self.nombre


class Piso(models.Model):
    nombre = models.CharField(max_length=50, unique=True, verbose_name="Nombre", help_text="Ej: Planta Baja, Piso 1")
    activo = models.BooleanField(default=True, verbose_name="Activo")

    class Meta:
        verbose_name = "Piso"
        verbose_name_plural = "Pisos"

    def __str__(self):
        return self.nombre


class Consultorio(models.Model):
    nombre_o_numero = models.CharField(max_length=50, verbose_name="Número o Nombre", help_text="Ej: Consultorio 101, Cama 5")
    piso            = models.ForeignKey(Piso, on_delete=models.CASCADE, related_name='consultorios', verbose_name="Piso")
    servicio        = models.ForeignKey(ServicioMedico, on_delete=models.CASCADE, related_name='consultorios', verbose_name="Servicio")
    activo          = models.BooleanField(default=True, verbose_name="Activo")

    class Meta:
        unique_together = ('nombre_o_numero', 'piso')
        verbose_name = "Consultorio"
        verbose_name_plural = "Consultorios"

    def __str__(self):
        return f"{self.nombre_o_numero} - {self.servicio.nombre} ({self.piso.nombre})"


class NormativaFinanciera(models.Model):
    nombre             = models.CharField(max_length=100, default="Tarifa", verbose_name="Nombre", help_text="Ej: Tarifa Base, Recargo Nocturno")
    hora_inicio        = models.TimeField(null=True, blank=True, verbose_name="Hora de Inicio", help_text="Aplica desde esta hora (opcional)")
    hora_fin           = models.TimeField(null=True, blank=True, verbose_name="Hora de Fin", help_text="Aplica hasta esta hora (opcional)")
    tarifa_por_hora    = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Tarifa por Hora (Bs.)", help_text="Pago por hora en Bolivianos")
    justificacion_legal = models.TextField(verbose_name="Justificación Legal", help_text="Ej: Ley General del Trabajo Art. 55")

    class Meta:
        verbose_name = "Normativa Financiera"
        verbose_name_plural = "Normativas Financieras"

    def __str__(self):
        rango = f" ({self.hora_inicio}–{self.hora_fin})" if self.hora_inicio and self.hora_fin else ""
        return f"{self.nombre}{rango}: Bs. {self.tarifa_por_hora}/h"


# ── Alias de compatibilidad (inglés → español) ────────────────────────────────
Fact                = Hecho
Rule                = Regla
MedicalService      = ServicioMedico
Floor               = Piso
ConsultingRoom      = Consultorio
FinancialNormative  = NormativaFinanciera
