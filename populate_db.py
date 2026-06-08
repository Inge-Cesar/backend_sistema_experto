import os
import django
import random
from datetime import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from modules.personal.models import Personal
from modules.base_conocimiento.models import ServicioMedico, Piso, Consultorio, NormativaFinanciera
from modules.turnos.models import AsignacionTurno
from django.contrib.auth import get_user_model

def populate():
    User = get_user_model()
    
    print("Limpiando datos antiguos...")
    AsignacionTurno.objects.all().delete()
    Consultorio.objects.all().delete()
    Piso.objects.all().delete()
    ServicioMedico.objects.all().delete()
    NormativaFinanciera.objects.all().delete()
    Personal.objects.all().delete()
    User.objects.all().delete()

    print("Creando usuario administrador...")
    User.objects.create_superuser(username='admin', email='admin@hospital.com', password='admin')

    print("Creando 15 Servicios Médicos...")
    services = []
    service_names = ["Pediatría", "Cardiología", "Neurología", "Traumatología", "Ginecología", 
                     "Dermatología", "Oftalmología", "Oncología", "Psiquiatría", "Urología",
                     "Endocrinología", "Gastroenterología", "Nefrología", "Neumología", "Reumatología"]
    for name in service_names:
        services.append(ServicioMedico.objects.create(nombre=name, descripcion=f"Servicio de {name}", capacidad_concurrente=random.randint(1, 5)))

    print("Creando 15 Pisos...")
    floors = []
    for i in range(1, 16):
        floors.append(Piso.objects.create(nombre=f"Piso {i}"))

    print("Creando 15 Consultorios...")
    rooms = []
    for i in range(1, 16):
        floor = random.choice(floors)
        service = random.choice(services)
        rooms.append(Consultorio.objects.create(
            nombre_o_numero=f"Consultorio {i*100 + random.randint(1,99)}",
            piso=floor,
            servicio=service
        ))

    print("Creando 15 Normativas Financieras...")
    normatives = []
    for i in range(1, 16):
        normatives.append(NormativaFinanciera.objects.create(
            nombre=f"Tarifa Especial {i}",
            hora_inicio=time(random.randint(0, 23), 0),
            hora_fin=time(random.randint(0, 23), 0),
            tarifa_por_hora=random.uniform(20.0, 150.0),
            justificacion_legal=f"Resolución Ministerial {i}/2023"
        ))

    print("Creando 15 Profesionales Médicos...")
    personnel_list = []
    first_names = ["Juan", "María", "Carlos", "Ana", "Luis", "Elena", "Pedro", "Laura", "Jorge", "Sofía", "Diego", "Carmen", "Miguel", "Lucía", "Andrés"]
    last_names = ["Gómez", "López", "Martínez", "Rodríguez", "Pérez", "Sánchez", "Romero", "Fernández", "García", "Torres", "Ruiz", "Díaz", "Álvarez", "Molina", "Castro"]
    
    for i in range(15):
        username = f"medico_{i}"
        user = User.objects.create_user(username=username, email=f"{username}@hospital.com", password="password123")
        
        personnel_list.append(Personal.objects.create(
            usuario=user,
            nombres=first_names[i],
            apellidos=last_names[i],
            cedula=f"{10000000+i}",
            especialidad=random.choice(["General", "Pediatra", "Cirujano", "Cardiólogo", "Neurólogo"]),
            horas_max_semanales=random.choice([36, 48, 60]),
            apto_nocturno=random.choice([True, True, False])
        ))

    print("Datos creados exitosamente.")

if __name__ == '__main__':
    populate()
