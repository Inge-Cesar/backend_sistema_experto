from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from datetime import datetime, timedelta, time
import random

from modules.personal.models import Personal
from modules.base_conocimiento.models import Consultorio
from modules.motor_experto.validators import validate_shift_assignment
from modules.auditoria.models import RegistroAuditoria
from .models import AsignacionTurno, SolicitudCambioTurno
from .serializers import AsignacionTurnoSerializer, SolicitudCambioTurnoSerializer


class AsignacionTurnoViewSet(viewsets.ModelViewSet):
    queryset = AsignacionTurno.objects.all()
    serializer_class = AsignacionTurnoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Filtrado opcional por rango de fechas.
        Ej: /api/turnos/?fecha_inicio=2026-05-01&fecha_fin=2026-05-31
        """
        queryset = super().get_queryset()
        fecha_inicio = self.request.query_params.get('start_date') or self.request.query_params.get('fecha_inicio')
        fecha_fin    = self.request.query_params.get('end_date')   or self.request.query_params.get('fecha_fin')

        if fecha_inicio and fecha_fin:
            queryset = queryset.filter(fecha__range=[fecha_inicio, fecha_fin])

        return queryset

    def perform_create(self, serializer):
        motivo = self.request.data.get('motivo', '')
        if not motivo:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({"motivo": "Debe justificar la creación manual de este turno."})
            
        turno = serializer.save()
        RegistroAuditoria.objects.create(
            usuario=self.request.user,
            accion='CREACION_TURNO_MANUAL',
            detalles=f"Se asignó un turno manual a {turno.personal.nombres} {turno.personal.apellidos} para el {turno.fecha} ({turno.hora_inicio}-{turno.hora_fin}) en el {turno.consultorio.nombre_o_numero}.",
            nivel_severidad='INFO',
            motivo=motivo
        )

    def destroy(self, request, *args, **kwargs):
        motivo = request.data.get('motivo', '')
        if not motivo:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({"motivo": "Debe justificar la eliminación de este turno."})
        return super().destroy(request, *args, **kwargs)

    def perform_destroy(self, instance):
        motivo = self.request.data.get('motivo', '')
        RegistroAuditoria.objects.create(
            usuario=self.request.user,
            accion='ELIMINACION_TURNO',
            detalles=f"Se eliminó el turno de {instance.personal.nombres} {instance.personal.apellidos} del {instance.fecha} ({instance.hora_inicio}).",
            nivel_severidad='ADVERTENCIA',
            motivo=motivo
        )
        super().perform_destroy(instance)

    @action(detail=False, methods=['post'])
    def auto_schedule(self, request):
        """Motor de Auto-Sugerencia: asigna turnos automáticamente respetando las reglas del Sistema Experto."""
        consultorio_id = request.data.get('consulting_room') or request.data.get('consultorio')
        fecha_inicio_str = request.data.get('start_date') or request.data.get('fecha_inicio')
        fecha_fin_str    = request.data.get('end_date')   or request.data.get('fecha_fin')

        if not all([consultorio_id, fecha_inicio_str, fecha_fin_str]):
            return Response(
                {"error": "Faltan parámetros: consultorio, fecha_inicio, fecha_fin"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            fecha_inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d').date()
            fecha_fin    = datetime.strptime(fecha_fin_str, '%Y-%m-%d').date()
            consultorio  = Consultorio.objects.get(id=consultorio_id)
        except Exception:
            return Response({"error": "Parámetros inválidos"}, status=status.HTTP_400_BAD_REQUEST)

        # Bloques de guardia propuestos
        bloques = [
            (time(8, 0),  time(16, 0)),
            (time(16, 0), time(0, 0)),
            (time(0, 0),  time(8, 0)),
        ]

        todo_el_personal = list(Personal.objects.all())
        turnos_creados = []
        explicaciones = []

        fecha_actual = fecha_inicio
        while fecha_actual <= fecha_fin:
            for inicio, fin in bloques:
                # Verificar si ya existe turno para ese bloque
                ya_existe = AsignacionTurno.objects.filter(
                    consultorio=consultorio,
                    fecha=fecha_actual,
                    hora_inicio=inicio
                ).exists()
                if ya_existe:
                    continue

                random.shuffle(todo_el_personal)
                bloque_str = f"{fecha_actual} ({inicio.strftime('%H:%M')} - {fin.strftime('%H:%M')})"
                
                explicaciones.append(f"\\n--- Evaluando bloque {bloque_str} ---")

                for persona in todo_el_personal:
                    es_valido, motivo = validate_shift_assignment(persona, fecha_actual, inicio, fin, consultorio)
                    if es_valido:
                        turno = AsignacionTurno.objects.create(
                            personal=persona,
                            consultorio=consultorio,
                            fecha=fecha_actual,
                            hora_inicio=inicio,
                            hora_fin=fin
                        )
                        turnos_creados.append(turno)
                        explicaciones.append(f"✅ Dr. {persona.nombres} {persona.apellidos} -> Asignado.")
                        break
                    else:
                        explicaciones.append(f"❌ Dr. {persona.nombres} {persona.apellidos} -> {motivo}")

            fecha_actual += timedelta(days=1)

        RegistroAuditoria.objects.create(
            usuario=request.user,
            accion='AUTO_ASIGNACION',
            detalles=f"El Motor Experto intentó generar turnos automáticamente desde el {fecha_inicio} al {fecha_fin} para el {consultorio.nombre_o_numero}. Se generaron {len(turnos_creados)} turnos nuevos.",
            nivel_severidad='INFO' if len(turnos_creados) > 0 else 'ADVERTENCIA'
        )

        serializer = self.get_serializer(turnos_creados, many=True)
        return Response({
            "mensaje": f"{len(turnos_creados)} turnos generados automáticamente.",
            "turnos": serializer.data,
            "explicaciones": explicaciones
        })

# Alias de compatibilidad
ShiftAssignmentViewSet = AsignacionTurnoViewSet

class SolicitudCambioTurnoViewSet(viewsets.ModelViewSet):
    queryset = SolicitudCambioTurno.objects.all()
    serializer_class = SolicitudCambioTurnoSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        swap = self.get_object()
        if swap.estado != 'Aceptado':
            return Response({"error": "Solo se pueden aprobar permutas aceptadas por un colega."}, status=400)
        
        # Efectuar el cambio real
        turno = swap.turno_original
        turno.personal = swap.medico_reemplazante
        turno.save()

        swap.estado = 'Aprobado_Admin'
        swap.save()
        
        RegistroAuditoria.objects.create(
            usuario=request.user,
            accion='APROBACION_PERMUTA',
            detalles=f"Se aprobó el cambio de turno ID {turno.id} de {swap.medico_solicitante.nombres} a {swap.medico_reemplazante.nombres}.",
            nivel_severidad='INFO'
        )

        return Response({"status": "Permuta aprobada exitosamente."})

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        swap = self.get_object()
        swap.estado = 'Rechazado'
        swap.save()
        
        RegistroAuditoria.objects.create(
            usuario=request.user,
            accion='RECHAZO_PERMUTA',
            detalles=f"Se rechazó el cambio de turno ID {swap.turno_original.id} solicitado por {swap.medico_solicitante.nombres}.",
            nivel_severidad='INFO'
        )
        return Response({"status": "Permuta rechazada."})
