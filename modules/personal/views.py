from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from core.permissions import IsAdminOrOwner, IsAdmin
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Personal, SolicitudPermiso
from .serializers import PersonalSerializer, SolicitudPermisoSerializer


class PersonalViewSet(viewsets.ModelViewSet):
    queryset = Personal.objects.all().order_by('-creado_en')
    serializer_class = PersonalSerializer
    permission_classes = [IsAuthenticated, IsAdminOrOwner]

    def get_queryset(self):
        # Si es admin, superuser o RRHH, puede ver todos. Si no, solo se ve a sí mismo
        user = self.request.user
        if user.is_superuser or (user.role and user.role.name in ['ADMIN', 'RRHH']):
            return Personal.objects.all().order_by('-creado_en')
        return Personal.objects.filter(usuario=user).order_by('-creado_en')


# Alias de compatibilidad
PersonnelViewSet = PersonalViewSet

class SolicitudPermisoViewSet(viewsets.ModelViewSet):
    queryset = SolicitudPermiso.objects.all().order_by('-fecha_solicitud')
    serializer_class = SolicitudPermisoSerializer
    permission_classes = [IsAuthenticated, IsAdminOrOwner]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or (user.role and user.role.name in ['ADMIN', 'RRHH']):
            return SolicitudPermiso.objects.all().order_by('-fecha_solicitud')
        return SolicitudPermiso.objects.filter(personal__usuario=user).order_by('-fecha_solicitud')

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsAdmin])
    def approve(self, request, pk=None):
        solicitud = self.get_object()
        solicitud.estado = 'Aprobado'
        solicitud.save()
        return Response({'status': 'Aprobado'})

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsAdmin])
    def reject(self, request, pk=None):
        solicitud = self.get_object()
        solicitud.estado = 'Rechazado'
        solicitud.save()
        return Response({'status': 'Rechazado'})
