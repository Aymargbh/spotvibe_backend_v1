"""
URLs pour l'application admin_dashboard.
"""

from django.urls import path
from . import views

urlpatterns = [
    # Dashboard principal
    path('dashboard/', views.dashboard_overview, name='admin-dashboard'),
    
    # Statistiques
    path('stats/users/', views.user_statistics, name='admin-user-stats'),
    path('stats/events/', views.event_statistics, name='admin-event-stats'),
    path('stats/payments/', views.payment_statistics, name='admin-payment-stats'),
    
    # Santé du système
    path('system/health/', views.system_health, name='admin-system-health'),
    
    # Actions
    path('actions/', views.AdminActionListView.as_view(), name='admin-actions'),
    path('bulk-action/', views.bulk_action, name='admin-bulk-action'),
    path('quick-action/', views.quick_action, name='admin-quick-action'),
    
    # Métriques
    path('metrics/', views.admin_metrics, name='admin-metrics'),
]