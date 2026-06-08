from rest_framework import serializers
from .models import ServicioMedico, NormativaFinanciera, Piso, Consultorio


class PisoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Piso
        fields = '__all__'


class ServicioMedicoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServicioMedico
        fields = '__all__'


class NormativaFinancieraSerializer(serializers.ModelSerializer):
    class Meta:
        model = NormativaFinanciera
        fields = '__all__'


class ConsultorioSerializer(serializers.ModelSerializer):
    detalles_piso     = PisoSerializer(source='piso', read_only=True)
    detalles_servicio = ServicioMedicoSerializer(source='servicio', read_only=True)

    class Meta:
        model = Consultorio
        fields = ['id', 'nombre_o_numero', 'piso', 'detalles_piso', 'servicio', 'detalles_servicio', 'activo']


# ── Alias de compatibilidad (inglés → español) ────────────────────────────────
FloorSerializer             = PisoSerializer
MedicalServiceSerializer    = ServicioMedicoSerializer
FinancialNormativeSerializer = NormativaFinancieraSerializer
ConsultingRoomSerializer    = ConsultorioSerializer

from .models import Regla
class ReglaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Regla
        fields = '__all__'
        
RuleSerializer = ReglaSerializer
