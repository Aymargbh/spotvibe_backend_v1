"""
Sérialiseurs pour l'application admin_dashboard.

Ce module définit les sérialiseurs Django REST Framework pour
le dashboard d'administration.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db.models import Count, Sum
from django.utils import timezone
from datetime import timedelta
from .models import AdminAction

User = get_user_model()


class AdminActionSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour les actions administratives.
    """
    
    utilisateur = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = AdminAction
        fields = [
            'id', 'utilisateur', 'action', 'description', 'cible_type',
            'cible_id', 'donnees_supplementaires', 'date_creation'
        ]
        read_only_fields = ['id', 'utilisateur', 'date_creation']


class DashboardStatsSerializer(serializers.Serializer):
    """
    Sérialiseur pour les statistiques du dashboard.
    """
    
    total_users = serializers.IntegerField()
    active_users = serializers.IntegerField()
    new_users_today = serializers.IntegerField()
    total_events = serializers.IntegerField()
    pending_events = serializers.IntegerField()
    approved_events = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=10, decimal_places=2)
    revenue_today = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_transactions = serializers.IntegerField()
    pending_verifications = serializers.IntegerField()


class UserStatsSerializer(serializers.Serializer):
    """
    Sérialiseur pour les statistiques des utilisateurs.
    """
    
    total_users = serializers.IntegerField()
    verified_users = serializers.IntegerField()
    unverified_users = serializers.IntegerField()
    active_users = serializers.IntegerField()
    inactive_users = serializers.IntegerField()
    users_by_subscription = serializers.DictField()
    new_users_last_30_days = serializers.ListField()


class EventStatsSerializer(serializers.Serializer):
    """
    Sérialiseur pour les statistiques des événements.
    """
    
    total_events = serializers.IntegerField()
    pending_events = serializers.IntegerField()
    approved_events = serializers.IntegerField()
    rejected_events = serializers.IntegerField()
    events_by_category = serializers.DictField()
    events_by_status = serializers.DictField()
    events_last_30_days = serializers.ListField()


class PaymentStatsSerializer(serializers.Serializer):
    """
    Sérialiseur pour les statistiques des paiements.
    """
    
    total_revenue = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_transactions = serializers.IntegerField()
    successful_transactions = serializers.IntegerField()
    failed_transactions = serializers.IntegerField()
    pending_transactions = serializers.IntegerField()
    revenue_by_method = serializers.DictField()
    revenue_last_30_days = serializers.ListField()


class SystemHealthSerializer(serializers.Serializer):
    """
    Sérialiseur pour la santé du système.
    """
    
    database_status = serializers.CharField()
    cache_status = serializers.CharField()
    storage_status = serializers.CharField()
    api_response_time = serializers.FloatField()
    error_rate = serializers.FloatField()
    uptime = serializers.CharField()


class BulkActionSerializer(serializers.Serializer):
    """
    Sérialiseur pour les actions en lot.
    """
    
    action = serializers.ChoiceField(choices=[
        'approve', 'reject', 'verify', 'suspend', 'activate'
    ])
    target_type = serializers.ChoiceField(choices=[
        'user', 'event', 'payment'
    ])
    target_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False
    )
    reason = serializers.CharField(required=False, allow_blank=True)
    
    def validate_target_ids(self, value):
        """Valide les IDs cibles."""
        if len(value) > 100:
            raise serializers.ValidationError(
                "Maximum 100 éléments par action en lot"
            )
        return value


class QuickActionSerializer(serializers.Serializer):
    """
    Sérialiseur pour les actions rapides.
    """
    
    action = serializers.ChoiceField(choices=[
        'approve_event', 'reject_event', 'verify_user', 'suspend_user',
        'process_payment', 'send_notification'
    ])
    target_id = serializers.IntegerField()
    data = serializers.JSONField(required=False)


class AdminMetricsSerializer(serializers.Serializer):
    """
    Sérialiseur pour les métriques administratives.
    """
    
    period = serializers.ChoiceField(choices=[
        'today', 'week', 'month', 'quarter', 'year'
    ])
    metric_type = serializers.ChoiceField(choices=[
        'users', 'events', 'payments', 'engagement'
    ])
    
    # Données de réponse
    labels = serializers.ListField(child=serializers.CharField(), read_only=True)
    data = serializers.ListField(child=serializers.IntegerField(), read_only=True)
    total = serializers.IntegerField(read_only=True)
    growth_rate = serializers.FloatField(read_only=True)


class AdminNotificationSerializer(serializers.Serializer):
    """
    Sérialiseur pour les notifications administratives.
    """
    
    title = serializers.CharField(max_length=200)
    message = serializers.CharField()
    type = serializers.ChoiceField(choices=[
        'info', 'warning', 'error', 'success'
    ])
    target_users = serializers.ListField(
        child=serializers.IntegerField(),
        required=False
    )
    target_groups = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )
    send_email = serializers.BooleanField(default=False)
    send_push = serializers.BooleanField(default=True)


class SystemConfigSerializer(serializers.Serializer):
    """
    Sérialiseur pour la configuration système.
    """
    
    maintenance_mode = serializers.BooleanField()
    registration_enabled = serializers.BooleanField()
    event_approval_required = serializers.BooleanField()
    max_file_size = serializers.IntegerField()
    allowed_file_types = serializers.ListField(
        child=serializers.CharField()
    )
    commission_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    notification_settings = serializers.JSONField()


class AdminReportSerializer(serializers.Serializer):
    """
    Sérialiseur pour les rapports administratifs.
    """
    
    report_type = serializers.ChoiceField(choices=[
        'users', 'events', 'payments', 'engagement', 'revenue'
    ])
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    format = serializers.ChoiceField(choices=['json', 'csv', 'pdf'])
    filters = serializers.JSONField(required=False)
    
    def validate(self, data):
        """Valide les dates."""
        if data['start_date'] > data['end_date']:
            raise serializers.ValidationError(
                "La date de début doit être antérieure à la date de fin"
            )
        
        # Limite à 1 an maximum
        if (data['end_date'] - data['start_date']).days > 365:
            raise serializers.ValidationError(
                "La période ne peut pas dépasser 1 an"
            )
        
        return data

