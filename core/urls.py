"""
URL configuration for backend_sistema_experto project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from modules.usuarios.views import CustomTokenObtainPairView
from modules.auditoria.views import HoneypotView
from django.http import HttpResponse

def run_seed(request):
    try:
        import seed_rules
        import seed_rules_2
        seed_rules_2.seed_nuevas_reglas()
        return HttpResponse("<h1>¡Reglas inyectadas exitosamente!</h1><p>Vuelve a tu panel y recarga la página.</p>")
    except Exception as e:
        return HttpResponse(f"<h1>Error:</h1><p>{e}</p>")

urlpatterns = [
    # TRAMPA PARA HACKERS (HONEYPOT) - Si una IP toca esta ruta, será bloqueada de por vida
    path('api/v1/hidden-admin-access/', HoneypotView.as_view(), name='honeypot'),

    path('admin/', admin.site.urls),
    # Endpoints de Autenticación JWT (Custom con Anti-Fuerza Bruta)
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    path('api/personnel/', include('modules.personal.urls')),
    path('api/mobile/', include('modules.personal.mobile_urls')),
    path('api/config/', include('modules.base_conocimiento.urls')),
    path('api/shifts/', include('modules.turnos.urls')),
    path('api/finance/', include('modules.turnos.finance_urls')),
    path('api/audit/', include('modules.auditoria.urls')),
    
    # RUTA TEMPORAL PARA SEMBRAR REGLAS
    path('setup-rules/', run_seed),
]

# Servir archivos multimedia (fotos de perfil) localmente sin MinIO (Incluso si DEBUG=False)
from django.conf import settings
from django.urls import re_path
from django.views.static import serve

    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]

def test_email_view(request):
    try:
        from django.core.mail import send_mail
        from django.conf import settings
        import traceback
        
        send_mail(
            'Prueba desde Render',
            'Este es un mensaje de prueba',
            settings.DEFAULT_FROM_EMAIL,
            ['hospital.experto@gmail.com'],
            fail_silently=False,
        )
        return HttpResponse("Correo enviado exitosamente")
    except Exception as e:
        import traceback
        return HttpResponse(f"Error al enviar correo: {traceback.format_exc()}")

urlpatterns += [
    path('test-email-render/', test_email_view),
]
