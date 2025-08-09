"""
URLs pour l'application payments.
"""

from django.urls import path
from . import views

urlpatterns = [
    # Paiements
    path('', views.PaymentListView.as_view(), name='payment-list'),
    path('initiate/', views.PaymentCreateView.as_view(), name='payment-create'),
    path('<uuid:uuid>/', views.PaymentDetailView.as_view(), name='payment-detail'),
    path('verify/', views.verify_payment, name='payment-verify'),
    path('cancel/', views.cancel_payment, name='payment-cancel'),
    path('retry/', views.retry_payment, name='payment-retry'),
    
    # Remboursements
    path('refunds/', views.RefundListView.as_view(), name='refund-list'),
    path('refunds/<int:pk>/', views.RefundDetailView.as_view(), name='refund-detail'),
    
    # Statistiques et informations
    path('stats/', views.payment_stats, name='payment-stats'),
    path('methods/', views.payment_methods, name='payment-methods'),
    path('summary/', views.user_payment_summary, name='payment-summary'),
    
    # Transactions et commissions
    path('transactions/', views.MomoTransactionListView.as_view(), name='transaction-list'),
    path('commissions/', views.CommissionListView.as_view(), name='commission-list'),
    
    # Webhooks Mobile Money
    path('webhooks/mtn/', views.mtn_money_webhook, name='mtn-webhook'),
    path('webhooks/moov/', views.moov_money_webhook, name='moov-webhook'),
]

