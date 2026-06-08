from django.http import JsonResponse
from django.conf import settings

class ApiKeyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Proteger todas las rutas de la API
        if request.path.startswith('/api/'):
            api_key = request.META.get('HTTP_X_API_KEY')
            if api_key != settings.GLOBAL_API_KEY:
                return JsonResponse(
                    {'error': 'Acceso denegado: API Key inválida o no proporcionada.'}, 
                    status=403
                )
        
        response = self.get_response(request)
        return response

class HoneypotMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Evitar importar a nivel de módulo para prevenir dependencias circulares
        from django.core.cache import cache
        from modules.auditoria.models import BlacklistedIP

        ip = self.get_client_ip(request)
        
        # Verificar si la IP está en caché (lista negra)
        cache_key = f'blacklist_ip_{ip}'
        is_blacklisted = cache.get(cache_key)

        if is_blacklisted is None:
            # Si no está en caché, chequear la base de datos
            if BlacklistedIP.objects.filter(ip_address=ip).exists():
                cache.set(cache_key, True, timeout=86400) # Cachear el baneo por 24 horas para ahorrar queries
                is_blacklisted = True
            else:
                cache.set(cache_key, False, timeout=300) # Cachear que es "limpio" por 5 min
                is_blacklisted = False

        if is_blacklisted:
            return JsonResponse({'error': '403 Forbidden - Access Denied by Security Policy'}, status=403)

        return self.get_response(request)

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
