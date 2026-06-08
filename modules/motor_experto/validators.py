from datetime import timedelta, datetime


def validate_shift_assignment(personal, fecha, hora_inicio, hora_fin, consultorio=None):
    """
    Motor Experto Clínico — Evalúa las reglas de producción para validar una asignación de turno.
    Devuelve (True, "") si es válido, o (False, "Motivo") si alguna regla bloquea la asignación.
    """
    from modules.turnos.models import AsignacionTurno
    from modules.base_conocimiento.models import Regla

    # Obtener nombres de reglas activas
    reglas_activas = set(Regla.objects.filter(activo=True).values_list('nombre', flat=True))

    # ── Preparación temporal ────────────────────────────────────────────────────
    turno_nocturno = hora_fin <= hora_inicio
    dt_inicio = datetime.combine(fecha, hora_inicio)
    dt_fin    = datetime.combine(
        fecha + timedelta(days=1) if turno_nocturno else fecha,
        hora_fin
    )
    duracion_horas = (dt_fin - dt_inicio).total_seconds() / 3600.0

    es_nocturno = turno_nocturno or hora_inicio.hour >= 22 or hora_inicio.hour < 6

    # ════════════════════════════════════════════════════════════════════════════
    # REGLAS DE BLOQUEO 🔴
    # ════════════════════════════════════════════════════════════════════════════

    # REGLA 2 — Límite semanal de horas (Ley del Trabajo, máx. 48 h/semana)
    if "Límite Legal (Máx 48h)" in reglas_activas:
        inicio_semana = fecha - timedelta(days=fecha.weekday())
        fin_semana    = inicio_semana + timedelta(days=6)
        turnos_semana = AsignacionTurno.objects.filter(
            personal=personal, fecha__range=[inicio_semana, fin_semana]
        )
        horas_semana = sum(
            (datetime.combine(
                t.fecha + timedelta(days=1) if t.hora_fin <= t.hora_inicio else t.fecha,
                t.hora_fin
            ) - datetime.combine(t.fecha, t.hora_inicio)).total_seconds() / 3600.0
            for t in turnos_semana
        )
        if horas_semana + duracion_horas > personal.horas_max_semanales:
            return False, (
                f"Regla 'Límite Legal (Máx 48h)' falló: Proyecta "
                f"{horas_semana + duracion_horas:.1f}h en la semana (límite: {personal.horas_max_semanales}h)."
            )

    # REGLA 3 — Descanso mínimo de 12 horas tras turno nocturno
    if "Descanso Mínimo (12h entre turnos)" in reglas_activas:
        for t in AsignacionTurno.objects.filter(personal=personal, fecha=fecha - timedelta(days=1)):
            if t.hora_fin <= t.hora_inicio or t.hora_inicio.hour >= 22:
                fin_anterior   = datetime.combine(fecha, t.hora_fin)
                descanso_horas = (dt_inicio - fin_anterior).total_seconds() / 3600.0
                if descanso_horas < 12:
                    return False, (
                        f"Regla 'Descanso Mínimo (12h entre turnos)' falló: "
                        f"Tuvo turno nocturno ayer. Descanso proyectado: {descanso_horas:.1f}h (min 12h)."
                    )

    # REGLA 6 — Turno nocturno sin aptitud nocturna
    if "Apto Médico Nocturno" in reglas_activas:
        if es_nocturno and not personal.apto_nocturno:
            return False, (
                f"Regla 'Apto Médico Nocturno' falló: "
                f"Turno es nocturno pero médico no tiene aptitud."
            )

    # REGLA 10 — Conflicto de horario (mismo profesional, bloque solapado)
    if "Prevención de Solapamiento" in reglas_activas:
        turnos_rango = AsignacionTurno.objects.filter(
            personal=personal,
            fecha__in=[fecha - timedelta(days=1), fecha, fecha + timedelta(days=1)]
        )
        for t in turnos_rango:
            t1 = datetime.combine(t.fecha, t.hora_inicio)
            t2 = datetime.combine(
                t.fecha + timedelta(days=1) if t.hora_fin <= t.hora_inicio else t.fecha,
                t.hora_fin
            )
            if max(dt_inicio, t1) < min(dt_fin, t2):
                return False, (
                    f"Regla 'Prevención de Solapamiento' falló: "
                    f"Ya tiene turno en {t.hora_inicio}-{t.hora_fin} el {t.fecha}."
                )

    # REGLA 4 — UCI requiere especialidad UCI
    if "Compatibilidad de Especialidad" in reglas_activas:
        if consultorio and consultorio.servicio.nombre.upper() in ('UCI', 'UNIDAD DE CUIDADOS INTENSIVOS'):
            esp = personal.especialidad.upper()
            if 'UCI' not in esp and 'INTENSIVO' not in esp:
                return False, (
                    f"Regla 'Compatibilidad de Especialidad' falló: "
                    f"Consultorio UCI requiere especialista UCI. El médico es '{personal.especialidad}'."
                )

    # REGLA 1 — Conflicto físico en consultorio (capacidad = 1 por bloque)
    if "Límite de Capacidad del Consultorio" in reglas_activas:
        if consultorio:
            for t in AsignacionTurno.objects.filter(
                consultorio=consultorio,
                fecha__in=[fecha - timedelta(days=1), fecha, fecha + timedelta(days=1)]
            ):
                t1 = datetime.combine(t.fecha, t.hora_inicio)
                t2 = datetime.combine(
                    t.fecha + timedelta(days=1) if t.hora_fin <= t.hora_inicio else t.fecha,
                    t.hora_fin
                )
                if max(dt_inicio, t1) < min(dt_fin, t2):
                    return False, (
                        f"Regla 'Límite de Capacidad del Consultorio' falló: "
                        f"'{consultorio.nombre_o_numero}' ya ocupado en ese horario."
                    )

    # Vacaciones / Permisos (Nuevas reglas)
    if "Bloqueo por Vacaciones" in reglas_activas:
        if personal.en_vacaciones:
            if not personal.fecha_fin_vacaciones or personal.fecha_fin_vacaciones >= fecha:
                return False, f"Regla 'Bloqueo por Vacaciones' falló: El médico está de vacaciones."
                
    if "Bloqueo por Permisos Médicos" in reglas_activas:
        if personal.permiso_activo:
            if not personal.fecha_fin_permiso or personal.fecha_fin_permiso >= fecha:
                return False, f"Regla 'Bloqueo por Permisos Médicos' falló: El médico tiene un permiso activo."

    # ════════════════════════════════════════════════════════════════════════════
    # REGLA 15 — Por Defecto: asignar con rotación equitativa ✅
    # ════════════════════════════════════════════════════════════════════════════
    return True, ""
