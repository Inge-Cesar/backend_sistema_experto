from rest_framework import serializers
from .models import AsignacionTurno
from modules.personal.serializers import PersonalSerializer
from modules.base_conocimiento.serializers import ConsultorioSerializer
from modules.motor_experto.validators import validate_shift_assignment
from .models import SolicitudCambioTurno


class AsignacionTurnoSerializer(serializers.ModelSerializer):
    detalles_personal    = PersonalSerializer(source='personal', read_only=True)
    detalles_consultorio = ConsultorioSerializer(source='consultorio', read_only=True)

    class Meta:
        model = AsignacionTurno
        fields = [
            'id',
            'personal', 'detalles_personal',
            'consultorio', 'detalles_consultorio',
            'fecha', 'hora_inicio', 'hora_fin',
            'creado_en'
        ]
        read_only_fields = ['id', 'creado_en']

    def validate(self, data):
        personal    = data.get('personal')    or (self.instance.personal    if self.instance else None)
        fecha       = data.get('fecha')       or (self.instance.fecha       if self.instance else None)
        hora_inicio = data.get('hora_inicio') or (self.instance.hora_inicio if self.instance else None)
        hora_fin    = data.get('hora_fin')    or (self.instance.hora_fin    if self.instance else None)
        consultorio = data.get('consultorio') or (self.instance.consultorio if self.instance else None)

        if hora_inicio and hora_fin:
            es_valido, mensaje_error = validate_shift_assignment(
                personal, fecha, hora_inicio, hora_fin, consultorio
            )
            if not es_valido:
                raise serializers.ValidationError({"rechazo_motor_experto": mensaje_error})

        return data


# Alias de compatibilidad
ShiftAssignmentSerializer = AsignacionTurnoSerializer

class SolicitudCambioTurnoSerializer(serializers.ModelSerializer):
    detalles_turno = AsignacionTurnoSerializer(source='turno_original', read_only=True)
    nombres_solicitante = serializers.SerializerMethodField()
    nombres_reemplazante = serializers.SerializerMethodField()

    class Meta:
        model = SolicitudCambioTurno
        fields = [
            'id', 'turno_original', 'detalles_turno',
            'medico_solicitante', 'nombres_solicitante',
            'medico_reemplazante', 'nombres_reemplazante',
            'motivo', 'estado', 'fecha_solicitud'
        ]
        read_only_fields = ['id', 'fecha_solicitud']

    def get_nombres_solicitante(self, obj):
        return f"{obj.medico_solicitante.nombres} {obj.medico_solicitante.apellidos}"

    def get_nombres_reemplazante(self, obj):
        if obj.medico_reemplazante:
            return f"{obj.medico_reemplazante.nombres} {obj.medico_reemplazante.apellidos}"
        return None
