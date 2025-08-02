"""
Sérialiseurs pour l'application notifications.

Ce module définit les sérialiseurs Django REST Framework pour
le système de notifications.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    Notification, NotificationPreference, NotificationTemplate,
    PushToken
)
from apps.users.serializers import UserPublicSerializer

User = get_user_model()


class NotificationSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour les notifications.
    """
    
    destinataire = UserPublicSerializer(read_only=True)
    
    class Meta:
        model = Notification
        fields = [
            'id', 'destinataire', 'titre', 'message', 'type_notification',
            'canal', 'statut', 'date_creation', 'date_lecture',
            'donnees_supplementaires', 'lien_action'
        ]
        read_only_fields = [
            'id', 'destinataire', 'date_creation', 'date_lecture'
        ]


class NotificationCreateSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour créer une notification.
    """
    
    destinataire_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = Notification
        fields = [
            'destinataire_id', 'titre', 'message', 'type_notification',
            'canal', 'donnees_supplementaires', 'lien_action'
        ]
    
    def validate_destinataire_id(self, value):
        """Valide le destinataire."""
        try:
            user = User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("Utilisateur introuvable")
        return value
    
    def create(self, validated_data):
        """Crée une notification."""
        destinataire_id = validated_data.pop('destinataire_id')
        destinataire = User.objects.get(id=destinataire_id)
        
        notification = Notification.objects.create(
            destinataire=destinataire,
            **validated_data
        )
        
        return notification


class NotificationTemplateSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour les templates de notifications.
    """
    
    class Meta:
        model = NotificationTemplate
        fields = [
            'id', 'nom', 'type_notification', 'titre_template',
            'message_template', 'variables', 'actif', 'date_creation',
            'date_modification'
        ]
        read_only_fields = ['id', 'date_creation', 'date_modification']


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour les préférences de notifications.
    """
    
    utilisateur = UserPublicSerializer(read_only=True)
    
    class Meta:
        model = NotificationPreference
        fields = [
            'id', 'utilisateur', 'email_notifications', 'push_notifications',
            'sms_notifications', 'in_app_notifications', 'evenements_suivis',
            'nouveaux_followers', 'messages_prives', 'promotions',
            'rappels_evenements', 'date_creation', 'date_modification'
        ]
        read_only_fields = [
            'id', 'utilisateur', 'date_creation', 'date_modification'
        ]


class NotificationPreferenceUpdateSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour mettre à jour les préférences de notifications.
    """
    
    class Meta:
        model = NotificationPreference
        fields = [
            'email_notifications', 'push_notifications', 'sms_notifications',
            'in_app_notifications', 'evenements_suivis', 'nouveaux_followers',
            'messages_prives', 'promotions', 'rappels_evenements'
        ]


class PushTokenSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour les tokens push.
    """
    
    utilisateur = UserPublicSerializer(read_only=True)
    
    class Meta:
        model = PushToken
        fields = [
            'id', 'utilisateur', 'token', 'plateforme', 'actif',
            'date_creation', 'date_derniere_utilisation'
        ]
        read_only_fields = [
            'id', 'utilisateur', 'date_creation', 'date_derniere_utilisation'
        ]


class PushTokenCreateSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour créer un token push.
    """
    
    class Meta:
        model = PushToken
        fields = ['token', 'plateforme']
    
    def validate_token(self, value):
        """Valide le token."""
        if not value or len(value) < 10:
            raise serializers.ValidationError("Token invalide")
        return value
    
    def create(self, validated_data):
        """Crée ou met à jour un token push."""
        user = self.context['request'].user
        token = validated_data['token']
        plateforme = validated_data['plateforme']
        
        # Désactiver les anciens tokens de cette plateforme
        PushToken.objects.filter(
            utilisateur=user,
            plateforme=plateforme
        ).update(actif=False)
        
        # Créer ou réactiver le token
        push_token, created = PushToken.objects.get_or_create(
            utilisateur=user,
            token=token,
            defaults={'plateforme': plateforme, 'actif': True}
        )
        
        if not created:
            push_token.actif = True
            push_token.plateforme = plateforme
            push_token.save()
        
        return push_token


class NotificationStatsSerializer(serializers.Serializer):
    """
    Sérialiseur pour les statistiques de notifications.
    """
    
    total_notifications = serializers.IntegerField()
    unread_notifications = serializers.IntegerField()
    notifications_today = serializers.IntegerField()
    notifications_by_type = serializers.DictField()
    notifications_by_status = serializers.DictField()


class BulkNotificationSerializer(serializers.Serializer):
    """
    Sérialiseur pour l'envoi en masse de notifications.
    """
    
    titre = serializers.CharField(max_length=200)
    message = serializers.CharField()
    type_notification = serializers.ChoiceField(
        choices=['SYSTEME', 'EVENEMENT', 'SOCIAL', 'PAIEMENT', 'PROMOTION']
    )
    canal = serializers.ChoiceField(
        choices=['EMAIL', 'PUSH', 'SMS', 'IN_APP']
    )
    destinataires = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False
    )
    donnees_supplementaires = serializers.JSONField(required=False)
    lien_action = serializers.URLField(required=False)
    
    def validate_destinataires(self, value):
        """Valide les destinataires."""
        if len(value) > 1000:
            raise serializers.ValidationError(
                "Maximum 1000 destinataires par envoi"
            )
        
        # Vérifier que tous les utilisateurs existent
        existing_users = User.objects.filter(id__in=value).count()
        if existing_users != len(value):
            raise serializers.ValidationError(
                "Certains utilisateurs n'existent pas"
            )
        
        return value


class NotificationMarkReadSerializer(serializers.Serializer):
    """
    Sérialiseur pour marquer des notifications comme lues.
    """
    
    notification_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False
    )
    
    def validate_notification_ids(self, value):
        """Valide les IDs de notifications."""
        user = self.context['request'].user
        
        # Vérifier que toutes les notifications appartiennent à l'utilisateur
        user_notifications = Notification.objects.filter(
            id__in=value,
            destinataire=user
        ).count()
        
        if user_notifications != len(value):
            raise serializers.ValidationError(
                "Certaines notifications ne vous appartiennent pas"
            )
        
        return value

