from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AuditoriaViewSet, DatabaseBackupView

router = DefaultRouter()
router.register(r'logs', AuditoriaViewSet, basename='auditoria')

urlpatterns = [
    path('backup/', DatabaseBackupView.as_view(), name='database_backup'),
    path('', include(router.urls)),
]
