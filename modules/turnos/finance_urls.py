from django.urls import path
from .finance_views import ReportePrenominaView

urlpatterns = [
    path('payroll/', ReportePrenominaView.as_view(), name='payroll-report'),
]
