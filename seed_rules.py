import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from modules.base_conocimiento.models import Regla

reglas_iniciales = [
    {"nombre": "Límite Legal (Máx 48h)", "descripcion": "Impide asignar turnos si el médico supera las 48 horas semanales permitidas por ley.", "prioridad": 100},
    {"nombre": "Descanso Mínimo (12h entre turnos)", "descripcion": "Bloquea turnos consecutivos que no respeten 12 horas de descanso ininterrumpido.", "prioridad": 95},
    {"nombre": "Compatibilidad de Especialidad", "descripcion": "Evita que un médico sea asignado a un servicio que no corresponde a su formación.", "prioridad": 90},
    {"nombre": "Prevención de Solapamiento", "descripcion": "Rechaza asignaciones si el médico ya tiene un turno cruzado en la misma fecha y hora.", "prioridad": 100},
    {"nombre": "Límite de Guardias Nocturnas Seguidas", "descripcion": "Restringe a 2 la cantidad máxima de noches consecutivas que puede hacer un residente.", "prioridad": 80},
    {"nombre": "Límite de Capacidad del Consultorio", "descripcion": "Bloquea que haya más médicos asignados de los que el consultorio soporta (Capacidad Concurrente).", "prioridad": 95},
    {"nombre": "Apto Médico Nocturno", "descripcion": "Restringe turnos de noche a personal marcado como 'No apto para nocturnidad'.", "prioridad": 90},
    {"nombre": "Equidad en Fines de Semana", "descripcion": "Asegura rotación justa y evita que el mismo médico trabaje todos los domingos.", "prioridad": 50},
    {"nombre": "Bloqueo por Vacaciones", "descripcion": "Bloquea la disponibilidad del médico durante su período de vacaciones aprobado.", "prioridad": 100},
    {"nombre": "Bloqueo por Permisos Médicos", "descripcion": "Inhabilita temporalmente al médico si está con licencia activa.", "prioridad": 100},
    {"nombre": "Continuidad de Cuidado (Misma Sala)", "descripcion": "Prioriza asignar al médico a su sala o consultorio habitual cuando sea posible.", "prioridad": 40},
    {"nombre": "Preferencia de Turno", "descripcion": "Da prioridad al horario de preferencia del médico si el motor tiene varias opciones (Mañana/Noche).", "prioridad": 30},
    {"nombre": "Prevención de Fatiga Acumulada", "descripcion": "Desvía asignaciones si el Índice de Fatiga del médico pasa del 75%.", "prioridad": 75},
    {"nombre": "Voluntariado en Feriados", "descripcion": "Prefiere asignar a médicos que se marcaron como 'Voluntarios para Feriados'.", "prioridad": 60},
    {"nombre": "Restricción de Edad/Riesgo", "descripcion": "Evita asignar guardias pesadas (ej. COVID) a personal mayor o en grupo de riesgo.", "prioridad": 85},
]

print("Inyectando reglas del Motor Experto...")
for r in reglas_iniciales:
    obj, created = Regla.objects.get_or_create(
        nombre=r['nombre'],
        defaults={
            'descripcion': r['descripcion'],
            'prioridad': r['prioridad'],
            'condicion': {},
            'accion': {},
            'activo': True
        }
    )
    if created:
        print(f"Creada: {obj.nombre}")
    else:
        print(f"Ya existía: {obj.nombre}")

print("Inyección completada exitosamente.")
