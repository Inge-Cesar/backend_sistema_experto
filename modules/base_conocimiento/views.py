from rest_framework import viewsets, permissions
from .models import ServicioMedico, NormativaFinanciera, Piso, Consultorio
from .serializers import (
    ServicioMedicoSerializer, NormativaFinancieraSerializer,
    PisoSerializer, ConsultorioSerializer
)


class ServicioMedicoViewSet(viewsets.ModelViewSet):
    queryset = ServicioMedico.objects.all()
    serializer_class = ServicioMedicoSerializer
    permission_classes = [permissions.IsAuthenticated]


class NormativaFinancieraViewSet(viewsets.ModelViewSet):
    queryset = NormativaFinanciera.objects.all()
    serializer_class = NormativaFinancieraSerializer
    permission_classes = [permissions.IsAuthenticated]


class PisoViewSet(viewsets.ModelViewSet):
    queryset = Piso.objects.all()
    serializer_class = PisoSerializer
    permission_classes = [permissions.IsAuthenticated]


class ConsultorioViewSet(viewsets.ModelViewSet):
    queryset = Consultorio.objects.all()
    serializer_class = ConsultorioSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        # Soporta filtros en español e inglés
        servicio_id = self.request.query_params.get('servicio') or self.request.query_params.get('service')
        piso_id     = self.request.query_params.get('piso')     or self.request.query_params.get('floor')
        if servicio_id:
            queryset = queryset.filter(servicio_id=servicio_id)
        if piso_id:
            queryset = queryset.filter(piso_id=piso_id)
        return queryset


# Aliases de compatibilidad
MedicalServiceViewSet    = ServicioMedicoViewSet
FinancialNormativeViewSet = NormativaFinancieraViewSet
FloorViewSet             = PisoViewSet
ConsultingRoomViewSet    = ConsultorioViewSet

from .models import Regla
from .serializers import ReglaSerializer

class ReglaViewSet(viewsets.ModelViewSet):
    queryset = Regla.objects.all().order_by('-prioridad', 'id')
    serializer_class = ReglaSerializer
    permission_classes = [permissions.IsAuthenticated]

RuleViewSet = ReglaViewSet
