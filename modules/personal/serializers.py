from rest_framework import serializers
from django.contrib.auth import get_user_model
from modules.usuarios.models import Role
from .models import Personal
from modules.turnos.models import AsignacionTurno
from datetime import timedelta, datetime, date

User = get_user_model()


class PersonalSerializer(serializers.ModelSerializer):
    nombres   = serializers.CharField(max_length=255)
    apellidos = serializers.CharField(max_length=255)
    cedula    = serializers.CharField(max_length=255)
    correo    = serializers.CharField(max_length=255, required=False, allow_blank=True)
    codigo_usuario = serializers.SerializerMethodField()
    indice_fatiga = serializers.SerializerMethodField()
    disponibilidad_dinamica = serializers.SerializerMethodField()

    class Meta:
        model = Personal
        fields = [
            'id', 'nombres', 'apellidos', 'cedula', 'correo', 'codigo_usuario',
            'especialidad', 'horas_max_semanales', 'apto_nocturno',
            'categoria', 'haber_basico', 'servicio_asignado', 'sala_habitual',
            'antiguedad_meses', 'voluntario_feriados', 'en_vacaciones',
            'fecha_fin_vacaciones', 'permiso_activo', 'fecha_fin_permiso',
            'foto', 'creado_en', 'indice_fatiga', 'disponibilidad_dinamica'
        ]
        read_only_fields = ['id', 'creado_en', 'codigo_usuario', 'disponibilidad_dinamica']

    def get_codigo_usuario(self, obj):
        if obj.usuario:
            return obj.usuario.username
        # Si fue recién creado y le inyectamos codigo_generado temporalmente
        if hasattr(obj, 'codigo_generado'):
            return obj.codigo_generado
        return None

    def get_indice_fatiga(self, obj):
        try:
            from datetime import datetime, date, timedelta
            from modules.turnos.models import AsignacionTurno
            import math
            
            hoy = date.today()
            hace_7_dias = hoy - timedelta(days=7)
            turnos_semana = AsignacionTurno.objects.filter(
                personal=obj, fecha__range=[hace_7_dias, hoy]
            ).order_by('fecha', 'hora_inicio')
            
            horas_trabajadas = 0
            penalizacion_nocturna = 0
            penalizacion_descanso = 0
            
            ultimo_fin_turno = None
            
            for t in turnos_semana:
                dt_inicio = datetime.combine(t.fecha, t.hora_inicio)
                dt_fin = datetime.combine(
                    t.fecha + timedelta(days=1) if t.hora_fin <= t.hora_inicio else t.fecha,
                    t.hora_fin
                )
                
                # Horas base
                horas_trabajadas += (dt_fin - dt_inicio).total_seconds() / 3600.0
                
                # Turno nocturno
                if t.hora_fin <= t.hora_inicio or t.hora_inicio.hour >= 22 or t.hora_inicio.hour < 6:
                    penalizacion_nocturna = 20
                    
                # Descanso corto (< 12 horas)
                if ultimo_fin_turno:
                    descanso = (dt_inicio - ultimo_fin_turno).total_seconds() / 3600.0
                    if descanso < 12 and descanso > 0:
                        penalizacion_descanso = 15
                        
                ultimo_fin_turno = dt_fin
                
            fatiga = math.floor(horas_trabajadas) + penalizacion_nocturna + penalizacion_descanso
            return fatiga
        except Exception:
            return 0

    def get_disponibilidad_dinamica(self, obj):
        return max(0, 100 - self.get_indice_fatiga(obj))

    def to_representation(self, instance):
        from django.utils import timezone
        from datetime import timedelta, datetime
        from modules.turnos.models import AsignacionTurno
        import math

        ret = super().to_representation(instance)
        
        # Inyectar el campo disponibilidad_dinamica = 100 - indice_fatiga
        fatiga = self.get_indice_fatiga(instance)
        disponibilidad = max(0, 100 - fatiga)
        ret['disponibilidad_dinamica'] = disponibilidad

        # Solo calcular detalles si los piden en endpoints específicos (el frontend actual usa estos)
        if hasattr(self, 'context') and self.context.get('request') and 'personal' in self.context.get('request').path:
            hoy = timezone.localdate()
            inicio_semana = hoy - timedelta(days=hoy.weekday())
            fin_semana = inicio_semana + timedelta(days=6)

            turnos = AsignacionTurno.objects.filter(
                personal=instance,
                fecha__range=[inicio_semana, fin_semana]
            )

            horas_totales = 0
            nocturnos = 0
            
            for t in turnos:
                dt_inicio = datetime.combine(t.fecha, t.hora_inicio)
                dt_fin = datetime.combine(
                    t.fecha + timedelta(days=1) if t.hora_fin <= t.hora_inicio else t.fecha,
                    t.hora_fin
                )
                horas = (dt_fin - dt_inicio).total_seconds() / 3600.0
                horas_totales += horas
                
                if t.hora_fin <= t.hora_inicio or t.hora_inicio.hour >= 22 or t.hora_inicio.hour < 6:
                    nocturnos += 1

            if fatiga < 40:
                nivel = "Apto"
            elif fatiga <= 60:
                nivel = "Precaución"
            else:
                nivel = "Riesgo"

            ret['horas_asignadas'] = round(horas_totales, 1)
            ret['turnos_nocturnos'] = nocturnos
            ret['puntos_estres'] = fatiga
            ret['nivel_estres'] = nivel

        return ret

    def create(self, validated_data):
        import random
        cedula = validated_data.get('cedula')
        # Obtener el password desde initial_data (ya que no está en Meta.fields)
        password = self.initial_data.get('password')
        if not password:
            password = cedula # Fallback por si acaso

        rol_medico, _ = Role.objects.get_or_create(name=Role.MEDICO)

        correo_input = validated_data.get('correo')
        email = correo_input if correo_input else f"{cedula}@hospital.bo"

        # Buscar si ya existe un usuario con este correo (ej. si fue eliminado el personal pero no el usuario)
        user = User.objects.filter(email=email).first()
        
        if user:
            if hasattr(user, 'perfil_personal'):
                raise serializers.ValidationError({"cedula": "Ya existe un médico registrado con este DNI o Correo electrónico."})
            created = False
            username = user.username
        else:
            # Generar Código de usuario numérico y único (Ej: MED-485930)
            while True:
                codigo_numerico = random.randint(100000, 999999)
                username = f"MED-{codigo_numerico}"
                if not User.objects.filter(username=username).exists():
                    break
            
            user = User.objects.create(
                username=username,
                email=email,
                role=rol_medico
            )
            created = True

        if password:
            user.set_password(password)
            user.save()

        personal = Personal.objects.create(usuario=user, **validated_data)
        
        # Opcional: Podríamos retornar el username generado en la respuesta
        # pero para no alterar la estructura, lo inyectamos al objeto
        personal.codigo_generado = username

        # Enviar correo de bienvenida si se registró un correo
        correo = validated_data.get('correo')
        if correo:
            from django.core.mail import send_mail
            from django.conf import settings
            import threading

            nombres = validated_data.get('nombres', '')
            apellidos = validated_data.get('apellidos', '')
            
            asunto = '🏥 Bienvenido al Sistema Experto del Hospital'
            mensaje = f'''Hola Dr/Dra. {nombres} {apellidos},

Se ha creado tu perfil laboral exitosamente en nuestro Sistema Experto de Asignación.
Para revisar tus horarios de guardia y llevar un control de tus ingresos, descarga nuestra App Móvil oficial.

Tus credenciales de acceso son:
Usuario (Código Médico): {username}
Contraseña temporal: {password}

Por tu seguridad, te recomendamos no compartir este correo.

Saludos cordiales,
Administración del Hospital.
'''
            def enviar_correo_async():
                try:
                    send_mail(
                        subject=asunto,
                        message=mensaje,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[correo],
                        fail_silently=True,
                    )
                except Exception as e:
                    print(f"Error al enviar correo: {e}")

            # Enviar de forma asíncrona para no bloquear la respuesta HTTP
            threading.Thread(target=enviar_correo_async).start()

        return personal

    def update(self, instance, validated_data):
        password = self.initial_data.get('password')
        if password:
            instance.usuario.set_password(password)
            instance.usuario.save()
        return super().update(instance, validated_data)


# Alias de compatibilidad
PersonnelSerializer = PersonalSerializer


class SolicitudPermisoSerializer(serializers.ModelSerializer):
    personal_nombre = serializers.CharField(source='personal.nombres', read_only=True)
    personal_apellido = serializers.CharField(source='personal.apellidos', read_only=True)
    especialidad = serializers.CharField(source='personal.especialidad', read_only=True)
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    personal_foto = serializers.SerializerMethodField()

    class Meta:
        model = __import__('modules.personal.models', fromlist=['SolicitudPermiso']).SolicitudPermiso
        fields = [
            'id', 'personal', 'personal_nombre', 'personal_apellido', 'especialidad', 'personal_foto',
            'tipo', 'tipo_display', 'fecha_inicio', 'fecha_fin', 'motivo', 
            'estado', 'fecha_solicitud'
        ]
        read_only_fields = ['estado', 'fecha_solicitud']

    def get_personal_foto(self, obj):
        if obj.personal.foto:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.personal.foto.url)
            return obj.personal.foto.url
        return None
