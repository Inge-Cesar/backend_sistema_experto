from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from datetime import date
from decimal import Decimal
from calendar import monthrange

from modules.turnos.models import AsignacionTurno
from modules.base_conocimiento.models import NormativaFinanciera
from modules.personal.models import Personal


def calcular_horas_turno(hora_inicio, hora_fin):
    from datetime import datetime as dt, timedelta
    base = date(2000, 1, 1)
    inicio_dt = dt.combine(base, hora_inicio)
    if hora_fin <= hora_inicio:
        fin_dt = dt.combine(base + timedelta(days=1), hora_fin)
    else:
        fin_dt = dt.combine(base, hora_fin)
    return round(Decimal(str((fin_dt - inicio_dt).total_seconds() / 3600)), 2)


def buscar_normativa_aplicable(hora_inicio, hora_fin, normativas):
    for norm in normativas:
        if norm.hora_inicio and norm.hora_fin:
            if norm.hora_inicio <= hora_inicio < norm.hora_fin:
                return norm
    for norm in normativas:
        if not norm.hora_inicio and not norm.hora_fin:
            return norm
    return normativas[0] if normativas else None


class ReportePrenominaView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Genera la prenómina del mes/año indicado.
        Parámetros: ?mes=5&anio=2026  (también acepta month/year para compatibilidad)
        """
        hoy = date.today()
        mes  = request.query_params.get('mes')  or request.query_params.get('month')
        anio = request.query_params.get('anio') or request.query_params.get('year')

        try:
            mes  = int(mes)  if mes  else hoy.month
            anio = int(anio) if anio else hoy.year
        except ValueError:
            return Response({"error": "Parámetros inválidos"}, status=400)

        _, dias_en_mes = monthrange(anio, mes)
        fecha_inicio = date(anio, mes, 1)
        fecha_fin    = date(anio, mes, dias_en_mes)

        turnos = AsignacionTurno.objects.filter(
            fecha__range=[fecha_inicio, fecha_fin]
        ).select_related('personal', 'consultorio', 'consultorio__servicio')

        normativas = list(NormativaFinanciera.objects.all())

        mapa_personal = {}
        todo_personal = Personal.objects.all()
        for persona in todo_personal:
            mapa_personal[persona.id] = {
                "id":           persona.id,
                "nombres":      persona.nombres,
                "apellidos":    persona.apellidos,
                "especialidad": persona.especialidad,
                "haber_basico": persona.haber_basico if persona.haber_basico else Decimal("0"),
                "total_horas":  Decimal("0"),
                "ingresos_guardias":  Decimal("0"),
                "total_pagar":  persona.haber_basico if persona.haber_basico else Decimal("0"),
                "cant_turnos":  0,
                "desglose":     []
            }

        for turno in turnos:
            pid = turno.personal.id
            if pid not in mapa_personal:
                continue

            horas   = calcular_horas_turno(turno.hora_inicio, turno.hora_fin)
            norma   = buscar_normativa_aplicable(turno.hora_inicio, turno.hora_fin, normativas)
            tarifa  = norma.tarifa_por_hora if norma else Decimal("0")
            bruto   = round(horas * tarifa, 2)

            mapa_personal[pid]["total_horas"] += horas
            mapa_personal[pid]["ingresos_guardias"] += bruto
            mapa_personal[pid]["total_pagar"] = mapa_personal[pid]["haber_basico"] + mapa_personal[pid]["ingresos_guardias"]
            mapa_personal[pid]["cant_turnos"] += 1
            mapa_personal[pid]["desglose"].append({
                "fecha":       str(turno.fecha),
                "hora_inicio": str(turno.hora_inicio)[:5],
                "hora_fin":    str(turno.hora_fin)[:5],
                "horas":       float(horas),
                "consultorio": turno.consultorio.nombre_o_numero,
                "servicio":    turno.consultorio.servicio.nombre,
                "normativa":   norma.nombre if norma else "Sin tarifa",
                "tarifa":      float(tarifa),
                "bruto":       float(bruto),
            })

        prenomina = sorted(
            mapa_personal.values(),
            key=lambda x: x["total_pagar"],
            reverse=True
        )
        for item in prenomina:
            item["total_horas"] = float(item["total_horas"])
            item["haber_basico"] = float(item["haber_basico"])
            item["ingresos_guardias"] = float(item["ingresos_guardias"])
            item["total_pagar"] = float(item["total_pagar"])

        total_horas  = sum(p["total_horas"]  for p in prenomina)
        total_basicos = sum(p["haber_basico"] for p in prenomina)
        total_guardias = sum(p["ingresos_guardias"] for p in prenomina)
        total_pagar  = sum(p["total_pagar"]  for p in prenomina)
        total_turnos = sum(p["cant_turnos"] for p in prenomina)

        MESES = ['Enero','Febrero','Marzo','Abril','Mayo','Junio',
                 'Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']

        return Response({
            "mes":    mes,
            "anio":   anio,
            "periodo": f"{fecha_inicio.strftime('%d/%m/%Y')} – {fecha_fin.strftime('%d/%m/%Y')}",
            "resumen": {
                "total_personal": len(prenomina),
                "total_turnos":   total_turnos,
                "total_horas":    round(total_horas, 2),
                "total_basicos":  round(total_basicos, 2),
                "total_guardias": round(total_guardias, 2),
                "total_pagar":    round(total_pagar, 2),
            },
            "prenomina": prenomina,
        })
