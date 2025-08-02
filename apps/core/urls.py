"""
URLs pour l'application core.
"""

from django.urls import path
from . import views

urlpatterns = [
    # Informations de l'application
    path('info/', views.app_info, name='app-info'),
    path('stats/', views.app_statistics, name='app-stats'),
    
    # Recherche et utilitaires
    path('search/', views.global_search, name='global-search'),
    path('upload/', views.upload_file, name='upload-file'),
    path('report/', views.report_content, name='report-content'),
    
    # Santé et maintenance
    path('health/', views.health_check, name='health-check'),
    path('maintenance/', views.maintenance_mode, name='maintenance-mode'),
    
    # Feedback et contact
    path('feedback/', views.submit_feedback, name='submit-feedback'),
    path('contact/', views.ContactMessageListView.as_view(), name='contact-messages'),
    
    # FAQ et paramètres
    path('faq/', views.FAQListView.as_view(), name='faq-list'),
    path('settings/', views.AppSettingsView.as_view(), name='app-settings'),
]