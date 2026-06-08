from rest_framework import viewsets, permissions
from core.permissions import IsAdmin
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from django.core.management import call_command
from django.http import HttpResponse
import io
import json
from datetime import datetime

from .models import RegistroAuditoria
from .serializers import RegistroAuditoriaSerializer

class AuditoriaViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Vista de solo lectura para los registros de auditoría.
    Solo administradores o usuarios autenticados deberían verlo.
    """
    queryset = RegistroAuditoria.objects.all()
    serializer_class = RegistroAuditoriaSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdmin]

class DatabaseBackupView(APIView):
    """
    Endpoint para realizar un respaldo completo (JSON dump) de la BD.
    Limitado a 1 ejecución por día por usuario para evitar ataques de agotamiento de recursos.
    """
    permission_classes = [permissions.IsAuthenticated, IsAdmin]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'backup'

    def get(self, request):
        try:
            # Capturar la salida de dumpdata
            output = io.StringIO()
            call_command('dumpdata', format='json', indent=2, stdout=output)
            
            # Crear la respuesta HTTP con el archivo
            response = HttpResponse(output.getvalue(), content_type='application/json')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            response['Content-Disposition'] = f'attachment; filename="backup_hospital_{timestamp}.json"'
            
            return response
        except Exception as e:
            return Response({'error': str(e)}, status=500)

class HoneypotView(APIView):
    """
    Trampa para escaneres (DirBuster, Nikto, etc).
    Cualquier IP que toque esta vista será añadida a la Lista Negra y bloqueada permanentemente.
    """
    authentication_classes = [] # No requiere auth, es público
    permission_classes = []

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')

    def get(self, request, *args, **kwargs):
        return self._trap(request)

    def post(self, request, *args, **kwargs):
        return self._trap(request)

    def _trap(self, request):
        from django.core.cache import cache
        from .models import BlacklistedIP
        
        ip = self.get_client_ip(request)
        
        # Registrar la IP en la base de datos
        BlacklistedIP.objects.get_or_create(
            ip_address=ip,
            defaults={'reason': 'Activó el Honeypot (Escáner Detectado)'}
        )
        
        # Actualizar la caché del middleware para bloquearlo instantáneamente
        cache.set(f'blacklist_ip_{ip}', True, timeout=86400)
        
        return Response(
            {"error": "Acceso restringido. Su dirección IP ha sido registrada y bloqueada por políticas de seguridad."}, 
            status=403
        )
