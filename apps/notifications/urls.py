"""
URLs pour l'application notifications.
"""

from django.urls import path
from . import views

urlpatterns = [
    # Notifications
    path('', views.NotificationListView.as_view(), name='notification-list'),
    path('<int:pk>/', views.NotificationDetailView.as_view(), name='notification-detail'),
    path('mark-read/', views.mark_notifications_read, name='notification-mark-read'),
    path('mark-all-read/', views.mark_all_read, name='notification-mark-all-read'),
    path('stats/', views.notification_stats, name='notification-stats'),
    path('unread-count/', views.unread_count, name='notification-unread-count'),
    path('test/', views.test_notification, name='notification-test'),
    path('<int:notification_id>/delete/', views.delete_notification, name='notification-delete'),
    
    # Préférences
    path('preferences/', views.NotificationPreferenceView.as_view(), name='notification-preferences'),
    
    # Templates
    path('templates/', views.NotificationTemplateListView.as_view(), name='notification-templates'),
    
    # Push tokens
    path('push-tokens/', views.PushTokenListView.as_view(), name='push-tokens'),
    
    # Actions administratives
    path('bulk-send/', views.send_bulk_notification, name='notification-bulk-send'),
]

