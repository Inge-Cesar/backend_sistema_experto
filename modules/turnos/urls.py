from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ShiftAssignmentViewSet, SolicitudCambioTurnoViewSet

router = DefaultRouter()
router.register(r'swaps', SolicitudCambioTurnoViewSet, basename='swaps')
router.register(r'', ShiftAssignmentViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
