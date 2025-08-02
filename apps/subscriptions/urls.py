"""
URLs pour l'application subscriptions.
"""

from django.urls import path
from . import views

urlpatterns = [
    # Plans d'abonnement
    path('plans/', views.SubscriptionPlanListView.as_view(), name='subscription-plans'),
    path('plans/<int:pk>/', views.SubscriptionPlanDetailView.as_view(), name='subscription-plan-detail'),
    path('compare/', views.plans_comparison, name='plans-comparison'),
    
    # Abonnements
    path('', views.SubscriptionListView.as_view(), name='subscription-list'),
    path('<int:pk>/', views.SubscriptionDetailView.as_view(), name='subscription-detail'),
    path('current/', views.current_subscription, name='current-subscription'),
    
    # Actions sur les abonnements
    path('renew/', views.renew_subscription, name='subscription-renew'),
    path('cancel/', views.cancel_subscription, name='subscription-cancel'),
    path('upgrade/', views.upgrade_subscription, name='subscription-upgrade'),
    path('pay/', views.pay_subscription, name='subscription-pay'),
    
    # Informations et statistiques
    path('usage/', views.subscription_usage, name='subscription-usage'),
    path('benefits/', views.subscription_benefits, name='subscription-benefits'),
    path('history/', views.SubscriptionHistoryListView.as_view(), name='subscription-history'),
    path('stats/', views.subscription_stats, name='subscription-stats'),
    
    # Webhooks
    path('activate-webhook/', views.activate_subscription_webhook, name='subscription-activate-webhook'),
]

