from rest_framework import serializers
from .models import RegistroAuditoria
from django.contrib.auth import get_user_model

class RegistroAuditoriaSerializer(serializers.ModelSerializer):
    usuario_nombre = serializers.SerializerMethodField()

    class Meta:
        model = RegistroAuditoria
        fields = ['id', 'usuario', 'usuario_nombre', 'accion', 'detalles', 'motivo', 'nivel_severidad', 'fecha']
        read_only_fields = fields

    def get_usuario_nombre(self, obj):
        if obj.usuario:
            return obj.usuario.username
        return "Sistema Automático"
