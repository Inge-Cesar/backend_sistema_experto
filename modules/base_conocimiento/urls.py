from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MedicalServiceViewSet, FinancialNormativeViewSet, FloorViewSet, ConsultingRoomViewSet, ReglaViewSet

router = DefaultRouter()
router.register(r'services', MedicalServiceViewSet)
router.register(r'normatives', FinancialNormativeViewSet)
router.register(r'floors', FloorViewSet)
router.register(r'rooms', ConsultingRoomViewSet)
router.register(r'rules', ReglaViewSet, basename='rules')

urlpatterns = [
    path('', include(router.urls)),
]
