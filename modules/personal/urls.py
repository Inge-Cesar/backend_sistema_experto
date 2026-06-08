from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PersonnelViewSet, SolicitudPermisoViewSet

router = DefaultRouter()
router.register(r'permissions', SolicitudPermisoViewSet, basename='permissions')
router.register(r'', PersonnelViewSet, basename='personnel')

urlpatterns = [
    path('', include(router.urls)),
]
