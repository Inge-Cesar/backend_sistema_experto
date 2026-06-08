from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed

class SingleSessionJWTAuthentication(JWTAuthentication):
    """
    Extensión de la autenticación JWT por defecto para aplicar la política
    de "Sesión Única por Usuario". Solo la última sesión iniciada es válida.
    """
    def get_user(self, validated_token):
        user = super().get_user(validated_token)
        
        # Extraer la huella de sesión inyectada en el JWT
        token_session_id = validated_token.get('session_id')
        
        # Si el token no tiene sesión o no coincide con la base de datos, fue revocado.
        if token_session_id and user.current_session_id != token_session_id:
            raise AuthenticationFailed(
                'Sesión expirada. Se ha iniciado sesión desde otro dispositivo o navegador.',
                code='session_revoked'
            )
            
        return user
