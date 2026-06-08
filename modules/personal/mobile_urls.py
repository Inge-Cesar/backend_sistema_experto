from django.urls import path
from .mobile_views import (
    MiPerfilMobileView, 
    MisTurnosMobileView, 
    SolicitudPermisoMobileView,
    CambioTurnoMobileView,
    CambioTurnoMobileView,
    AceptarCambioMobileView,
    RequestOTPMobileView,
    LoginOTPMobileView
)

urlpatterns = [
    path('me/', MiPerfilMobileView.as_view(), name='mobile_me'),
    path('my-shifts/', MisTurnosMobileView.as_view(), name='mobile_my_shifts'),
    path('permissions/', SolicitudPermisoMobileView.as_view(), name='mobile_permissions'),
    path('shift-swaps/', CambioTurnoMobileView.as_view(), name='mobile_shift_swaps'),
    path('shift-swaps/<int:pk>/accept/', AceptarCambioMobileView.as_view(), name='mobile_accept_shift_swap'),
    path('request-otp/', RequestOTPMobileView.as_view(), name='mobile_request_otp'),
    path('login-otp/', LoginOTPMobileView.as_view(), name='mobile_login_otp'),
]
