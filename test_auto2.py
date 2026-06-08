import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from modules.turnos.models import AsignacionTurno
print("Turnos en BD:", AsignacionTurno.objects.count())
for t in AsignacionTurno.objects.all():
    print(t.fecha, t.hora_inicio, t.hora_fin, t.consultorio.nombre_o_numero)
