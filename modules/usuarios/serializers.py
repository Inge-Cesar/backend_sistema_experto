from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import exceptions
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model

User = get_user_model()

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        username_input = attrs.get('username')
        password = attrs.get('password')

        try:
            # Buscar por email o username (como el frontend manda el correo, probar email primero)
            user = User.objects.get(email=username_input)
        except User.DoesNotExist:
            try:
                user = User.objects.get(username=username_input)
            except User.DoesNotExist:
                raise exceptions.AuthenticationFailed('Credenciales inválidas.')

        if user.locked_until and user.locked_until > timezone.now():
            remaining = (user.locked_until - timezone.now()).seconds
            raise exceptions.AuthenticationFailed(f'Cuenta bloqueada por seguridad. Intente en {remaining} segundos.')

        if not user.check_password(password):
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= 5:
                user.locked_until = timezone.now() + timedelta(minutes=1)
                user.is_locked = True
                user.save()
                raise exceptions.AuthenticationFailed('Demasiados intentos fallidos. Cuenta bloqueada por 1 minuto.')
            user.save()
            raise exceptions.AuthenticationFailed(f'Credenciales inválidas. Intentos restantes: {5 - user.failed_login_attempts}')

        # Éxito
        user.failed_login_attempts = 0
        user.is_locked = False
        user.locked_until = None
        user.save()

        # Inyectar el username real para que la validación nativa de SimpleJWT funcione
        attrs['username'] = user.username

        return super().validate(attrs)

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        
        import uuid
        session_id = str(uuid.uuid4())
        
        # Inyectar en el JWT payload
        token['session_id'] = session_id
        
        # Guardar en la Base de Datos para invalidar sesiones previas
        user.current_session_id = session_id
        user.save(update_fields=['current_session_id'])
        
        return token
