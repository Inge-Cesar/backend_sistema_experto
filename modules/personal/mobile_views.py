from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers
from datetime import datetime, timedelta
from django.db.models import F
from modules.turnos.models import AsignacionTurno, SolicitudCambioTurno
from modules.personal.models import Personal, SolicitudPermiso

class MiPerfilMobileView(APIView):
    permission_classes = [IsAuthenticated]

    @method_decorator(cache_page(60 * 5))  # Caché de 5 minutos
    @method_decorator(vary_on_headers('Authorization'))
    def get(self, request):
        try:
            personal = request.user.perfil_personal
            
            # Calcular ingresos del mes actual y fatiga
            hoy = datetime.now()
            turnos_mes = AsignacionTurno.objects.filter(
                personal=personal,
                fecha__year=hoy.year,
                fecha__month=hoy.month
            )
            
            horas_trabajadas = 0
            turnos_nocturnos = 0
            for turno in turnos_mes:
                horas = (turno.hora_fin.hour - turno.hora_inicio.hour)
                if horas < 0: horas += 24 # Cruzó medianoche
                horas_trabajadas += horas
                es_nocturno = turno.hora_inicio.hour >= 20 or turno.hora_inicio.hour < 6 or turno.hora_fin.hour <= 8
                if es_nocturno:
                    turnos_nocturnos += 1

            # Lógica simple financiera/fatiga para la App
            pago_base_hora = 50.0  # Bs por hora
            pago_nocturno_extra = 20.0
            
            ingresos_estimados = (horas_trabajadas * pago_base_hora) + (turnos_nocturnos * 8 * pago_nocturno_extra)
            
            
            # Puntos de estrés (0 a 100)
            puntos_estres = min(100, int((horas_trabajadas / personal.horas_max_semanales) * 100 / 4))

            return Response({
                "id": personal.id,
                "nombres": personal.nombres,
                "apellidos": personal.apellidos,
                "especialidad": personal.especialidad,
                "foto": request.build_absolute_uri(personal.foto.url) if personal.foto else None,
                "correo": personal.correo,
                "allow_otp_login": request.user.allow_otp_login,
                "estadisticas": {
                    "horas_mes": horas_trabajadas,
                    "ingresos_estimados": float(ingresos_estimados),
                    "puntos_estres": puntos_estres,
                    "limite_semanal": personal.horas_max_semanales
                }
            })
        except Personal.DoesNotExist:
            return Response({"error": "No tiene perfil médico asociado."}, status=400)

    def post(self, request):
        try:
            personal = request.user.perfil_personal
            user = request.user
            
            correo = request.data.get('correo')
            password = request.data.get('password')
            allow_otp_login = request.data.get('allow_otp_login')
            
            cambios = []
            
            if correo and correo != personal.correo:
                personal.correo = correo
                user.email = correo
                cambios.append("Correo electrónico actualizado")
                
            if allow_otp_login is not None and str(allow_otp_login).lower() != str(user.allow_otp_login).lower():
                is_allowed = str(allow_otp_login).lower() in ['true', '1', 'yes']
                user.allow_otp_login = is_allowed
                cambios.append(f"Ingreso rápido (OTP) {'habilitado' if is_allowed else 'deshabilitado'}")

            if password:
                user.set_password(password)
                cambios.append("Contraseña actualizada")
                
            if cambios:
                personal.save()
                user.save()
                
                # Enviar correo de notificación
                if personal.correo:
                    from django.core.mail import send_mail
                    from django.conf import settings
                    import threading
                    
                    asunto = '🔒 Actualización de Seguridad - Sistema Experto'
                    mensaje = f'''Hola Dr/Dra. {personal.nombres} {personal.apellidos},

Te informamos que se han realizado los siguientes cambios en tu perfil de la aplicación móvil:
- {', '.join(cambios)}.

Si no fuiste tú quien realizó estos cambios, por favor contacta a la administración de inmediato.

Saludos cordiales,
Administración del Hospital.
'''
                    def enviar_correo_async():
                        try:
                            send_mail(
                                subject=asunto,
                                message=mensaje,
                                from_email=settings.DEFAULT_FROM_EMAIL,
                                recipient_list=[personal.correo],
                                fail_silently=True,
                            )
                        except Exception as e:
                            print(f"Error al enviar correo: {e}")

                    threading.Thread(target=enviar_correo_async).start()

                return Response({"success": "Perfil actualizado correctamente"}, status=200)
            
            return Response({"message": "No se recibieron cambios"}, status=200)
            
        except Personal.DoesNotExist:
            return Response({"error": "No tiene perfil médico asociado."}, status=400)
        except Exception as e:
            return Response({"error": str(e)}, status=400)


class MisTurnosMobileView(APIView):
    permission_classes = [IsAuthenticated]

    @method_decorator(cache_page(60 * 5))  # Caché de 5 minutos
    @method_decorator(vary_on_headers('Authorization'))
    def get(self, request):
        try:
            personal = request.user.perfil_personal
            hoy = datetime.now().date()
            
            # Solo enviar turnos de hoy en adelante para la App
            turnos = AsignacionTurno.objects.filter(
                personal=personal,
                fecha__gte=hoy
            ).order_by('fecha', 'hora_inicio')

            data = []
            for t in turnos:
                data.append({
                    "id": t.id,
                    "fecha": str(t.fecha),
                    "hora_inicio": str(t.hora_inicio)[:5],
                    "hora_fin": str(t.hora_fin)[:5],
                    "tipo_turno": 'NOCTURNO' if (t.hora_inicio.hour >= 20 or t.hora_inicio.hour < 6 or t.hora_fin.hour <= 8) else 'DIURNO',
                    "consultorio": t.consultorio.nombre_o_numero if t.consultorio else "General",
                    "piso": t.consultorio.piso.nombre if t.consultorio else "Planta Baja"
                })
                
            return Response(data)
        except Personal.DoesNotExist:
            return Response({"error": "No tiene perfil médico asociado."}, status=400)


class SolicitudPermisoMobileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            personal = request.user.perfil_personal
            solicitudes = SolicitudPermiso.objects.filter(personal=personal).order_by('-fecha_solicitud')
            data = []
            for s in solicitudes:
                data.append({
                    "id": s.id,
                    "tipo": s.get_tipo_display(),
                    "fecha_inicio": str(s.fecha_inicio),
                    "fecha_fin": str(s.fecha_fin),
                    "motivo": s.motivo,
                    "estado": s.estado,
                    "fecha_solicitud": str(s.fecha_solicitud.date())
                })
            return Response(data)
        except Personal.DoesNotExist:
            return Response({"error": "Perfil no encontrado"}, status=400)

    def post(self, request):
        try:
            personal = request.user.perfil_personal
            tipo = request.data.get('tipo')
            fecha_inicio = request.data.get('fecha_inicio')
            fecha_fin = request.data.get('fecha_fin')
            motivo = request.data.get('motivo')

            if not all([tipo, fecha_inicio, fecha_fin, motivo]):
                return Response({"error": "Todos los campos son obligatorios"}, status=400)

            SolicitudPermiso.objects.create(
                personal=personal,
                tipo=tipo,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                motivo=motivo,
                estado='Pendiente'
            )
            return Response({"success": "Solicitud enviada correctamente"}, status=201)
        except Exception as e:
            return Response({"error": str(e)}, status=400)


class CambioTurnoMobileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            personal = request.user.perfil_personal
            ahora = datetime.now()
            limite_24h = ahora + timedelta(hours=24)

            # Mis solicitudes
            mis_solicitudes_qs = SolicitudCambioTurno.objects.filter(medico_solicitante=personal).order_by('-fecha_solicitud')
            mis_solicitudes = []
            for s in mis_solicitudes_qs:
                dt_turno = datetime.combine(s.turno_original.fecha, s.turno_original.hora_inicio)
                # Si está pendiente y pasaron las 24 hrs límite, mostrar como Vencido
                estado_mostrar = s.estado
                if s.estado == 'Pendiente' and dt_turno < limite_24h:
                    estado_mostrar = 'Rechazado' # Vencido visualmente

                mis_solicitudes.append({
                    "id": s.id,
                    "fecha_turno": str(s.turno_original.fecha),
                    "hora_inicio": str(s.turno_original.hora_inicio)[:5],
                    "hora_fin": str(s.turno_original.hora_fin)[:5],
                    "consultorio": s.turno_original.consultorio.nombre_o_numero if s.turno_original.consultorio else "General",
                    "estado": estado_mostrar,
                    "reemplazante": f"{s.medico_reemplazante.nombres} {s.medico_reemplazante.apellidos}" if s.medico_reemplazante else None,
                    "motivo": s.motivo,
                    "fecha_solicitud": str(s.fecha_solicitud.date())
                })

            # Solicitudes disponibles (de otros)
            disponibles_qs = SolicitudCambioTurno.objects.filter(estado='Pendiente').exclude(medico_solicitante=personal).order_by('-fecha_solicitud')
            disponibles = []
            for s in disponibles_qs:
                dt_turno = datetime.combine(s.turno_original.fecha, s.turno_original.hora_inicio)
                if dt_turno >= limite_24h:
                    disponibles.append({
                        "id": s.id,
                        "medico_solicitante": f"{s.medico_solicitante.nombres} {s.medico_solicitante.apellidos}",
                        "fecha_turno": str(s.turno_original.fecha),
                        "hora_inicio": str(s.turno_original.hora_inicio)[:5],
                        "hora_fin": str(s.turno_original.hora_fin)[:5],
                        "consultorio": s.turno_original.consultorio.nombre_o_numero if s.turno_original.consultorio else "General",
                        "motivo": s.motivo,
                        "fecha_solicitud": str(s.fecha_solicitud.date())
                    })

            return Response({
                "mis_solicitudes": mis_solicitudes,
                "disponibles": disponibles
            })

        except Personal.DoesNotExist:
            return Response({"error": "Perfil no encontrado"}, status=400)

    def post(self, request):
        try:
            personal = request.user.perfil_personal
            turno_id = request.data.get('turno_id')
            motivo = request.data.get('motivo')

            if not turno_id or not motivo:
                return Response({"error": "Turno y motivo son obligatorios"}, status=400)

            try:
                turno = AsignacionTurno.objects.get(id=turno_id, personal=personal)
            except AsignacionTurno.DoesNotExist:
                return Response({"error": "Turno no encontrado o no te pertenece"}, status=404)

            # Verificar regla de 24 hrs
            ahora = datetime.now()
            dt_turno = datetime.combine(turno.fecha, turno.hora_inicio)
            if dt_turno < ahora + timedelta(hours=24):
                return Response({"error": "Debe solicitar el cambio con al menos 24 horas de anticipación"}, status=400)

            # Verificar si ya tiene solicitud
            if SolicitudCambioTurno.objects.filter(turno_original=turno, estado='Pendiente').exists():
                return Response({"error": "Ya existe una solicitud pendiente para este turno"}, status=400)

            SolicitudCambioTurno.objects.create(
                turno_original=turno,
                medico_solicitante=personal,
                motivo=motivo,
                estado='Pendiente'
            )
            return Response({"success": "Solicitud de cambio creada correctamente"}, status=201)
        except Exception as e:
            return Response({"error": str(e)}, status=400)


class AceptarCambioMobileView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            personal = request.user.perfil_personal
            try:
                solicitud = SolicitudCambioTurno.objects.get(id=pk, estado='Pendiente')
            except SolicitudCambioTurno.DoesNotExist:
                return Response({"error": "La solicitud no existe, ya fue aceptada o venció"}, status=404)

            if solicitud.medico_solicitante == personal:
                return Response({"error": "No puedes aceptar tu propia solicitud"}, status=400)

            # Verificar regla de 24 hrs
            ahora = datetime.now()
            dt_turno = datetime.combine(solicitud.turno_original.fecha, solicitud.turno_original.hora_inicio)
            if dt_turno < ahora + timedelta(hours=24):
                solicitud.estado = 'Rechazado'
                solicitud.save()
                return Response({"error": "Expiró el tiempo límite para aceptar este cambio (menos de 24hrs)"}, status=400)

            solicitud.estado = 'Aceptado'
            solicitud.medico_reemplazante = personal
            solicitud.save()

            return Response({"success": "Cambio aceptado correctamente. Pendiente de aprobación por el Administrador."}, status=200)

        except Exception as e:
            return Response({"error": str(e)}, status=400)

class RequestOTPMobileView(APIView):
    permission_classes = []

    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({"error": "Debe proporcionar un correo electrónico"}, status=400)
            
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"success": "Si el correo está registrado, recibirás un código"}, status=200)
            
        if not user.allow_otp_login:
            return Response({"error": "El inicio de sesión rápido (OTP) no está habilitado para esta cuenta. Ingrese con contraseña y habilítelo en ajustes."}, status=403)
            
        import random
        import string
        from django.utils import timezone
        
        otp = ''.join(random.choices(string.digits, k=6))
        user.otp_code = otp
        user.otp_created_at = timezone.now()
        user.save()
        
        # Enviar correo asíncrono
        from django.core.mail import send_mail
        from django.conf import settings
        import threading
        
        asunto = 'Su código de acceso - Sistema Experto'
        mensaje = f'Su código de acceso rápido (OTP) es: {otp}\n\nEste código expirará en 5 minutos.'
        
        def enviar_correo_async():
            try:
                send_mail(
                    subject=asunto,
                    message=mensaje,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=True,
                )
            except Exception as e:
                print(f"Error enviando OTP: {e}")
                
        threading.Thread(target=enviar_correo_async).start()
        
        return Response({"success": "Si el correo está registrado, recibirás un código"}, status=200)


class LoginOTPMobileView(APIView):
    permission_classes = []

    def post(self, request):
        email = request.data.get('email')
        otp = request.data.get('otp')
        
        if not email or not otp:
            return Response({"error": "Falta correo o código OTP"}, status=400)
            
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "Código o correo inválido"}, status=401)
            
        if not user.otp_code or user.otp_code != otp:
            return Response({"error": "Código incorrecto"}, status=401)
            
        from django.utils import timezone
        from datetime import timedelta
        
        if not user.otp_created_at or timezone.now() > user.otp_created_at + timedelta(minutes=5):
            return Response({"error": "El código ha expirado. Solicite uno nuevo."}, status=401)
            
        # Código válido, generar tokens
        user.otp_code = None
        user.otp_created_at = None
        user.save()
        
        from modules.usuarios.serializers import CustomTokenObtainPairSerializer
        token = CustomTokenObtainPairSerializer.get_token(user)
        
        return Response({
            'refresh': str(token),
            'access': str(token.access_token),
        })
