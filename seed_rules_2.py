import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from modules.base_conocimiento.models import Regla

def seed_nuevas_reglas():
    nuevas_reglas = [
        {
            "nombre": "Festivo sin Voluntariado",
            "descripcion": "Penaliza enormemente asignar un turno en día festivo a un médico que no está marcado como voluntario para feriados.",
            "prioridad": 80,
            "condicion": {
                "AND": [
                    {"field": "is_holiday", "operator": "is_true"},
                    {"field": "voluntario_feriados", "operator": "is_false"}
                ]
            },
            "accion": {"type": "ADD_FATIGUE", "value": 50}
        },
        {
            "nombre": "Novato en Servicio Complejo",
            "descripcion": "Añade estrés si el médico tiene menos de 6 meses de antigüedad y se le asigna a un servicio complejo (ej. UCI, Urgencias).",
            "prioridad": 60,
            "condicion": {
                "AND": [
                    {"field": "antiguedad_meses", "operator": "<", "value": 6},
                    {"field": "is_complex_service", "operator": "is_true"}
                ]
            },
            "accion": {"type": "ADD_FATIGUE", "value": 15}
        },
        {
            "nombre": "Excepción por Emergencia Alta",
            "descripcion": "Si el contexto marca una emergencia de nivel ALTA, se reduce artificialmente la fatiga a la mitad para permitir la asignación de médicos que normalmente estarían en amarillo.",
            "prioridad": 90,
            "condicion": {
                "field": "emergency_level", "operator": "==", "value": "ALTA"
            },
            "accion": {"type": "MULTIPLY_FATIGUE", "value": 0.5}
        },
        {
            "nombre": "Veterano en Servicio Crítico",
            "descripcion": "Si el médico tiene más de 5 años de antigüedad y el servicio es complejo, su tolerancia al estrés es mayor (reduce fatiga).",
            "prioridad": 65,
            "condicion": {
                "AND": [
                    {"field": "antiguedad_meses", "operator": ">=", "value": 60},
                    {"field": "is_complex_service", "operator": "is_true"}
                ]
            },
            "accion": {"type": "ADD_FATIGUE", "value": -10}
        },
        {
            "nombre": "Rotación Equitativa Preventiva",
            "descripcion": "Penaliza levemente si ha pasado menos de 2 días desde su último turno, para fomentar la asignación a otros médicos disponibles.",
            "prioridad": 40,
            "condicion": {
                "field": "days_since_last_shift", "operator": "<", "value": 2
            },
            "accion": {"type": "ADD_FATIGUE", "value": 10}
        }
    ]

    for rg in nuevas_reglas:
        Regla.objects.update_or_create(
            nombre=rg['nombre'],
            defaults={
                'descripcion': rg['descripcion'],
                'prioridad': rg['prioridad'],
                'condicion': rg['condicion'],
                'accion': rg['accion'],
                'activo': True
            }
        )
        print(f"Regla insertada/actualizada: {rg['nombre']}")

if __name__ == '__main__':
    seed_nuevas_reglas()
    print("Nuevas reglas sembradas exitosamente.")
