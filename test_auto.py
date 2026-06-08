import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from modules.base_conocimiento.models import Consultorio
from modules.personal.models import Personal
from modules.turnos.models import AsignacionTurno
from modules.motor_experto.validators import validate_shift_assignment
from datetime import date, time

print("Consultorios:", Consultorio.objects.count())
print("Personal:", Personal.objects.count())

c = Consultorio.objects.first()
p = Personal.objects.first()

print("Validando...", validate_shift_assignment(p, date(2026, 6, 1), time(8,0), time(16,0), c))
