"""
Sérialiseurs pour l'application core.

Ce module définit les sérialiseurs Django REST Framework pour
les fonctionnalités de base de l'application.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import AppSettings, ContactMessage, FAQ

User = get_user_model()


class AppSettingsSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour les paramètres de l'application.
    """
    
    class Meta:
        model = AppSettings
        fields = [
            'id', 'nom_app', 'version', 'description', 'email_contact',
            'telephone_contact', 'adresse', 'site_web', 'maintenance_mode',
            'message_maintenance', 'inscription_ouverte', 'commission_defaut',
            'taille_max_fichier', 'types_fichiers_autorises', 'date_creation',
            'date_modification'
        ]
        read_only_fields = ['id', 'date_creation', 'date_modification']


class ContactMessageSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour les messages de contact.
    """
    
    class Meta:
        model = ContactMessage
        fields = [
            'id', 'nom', 'email', 'sujet', 'message', 'statut',
            'date_creation', 'date_traitement', 'reponse'
        ]
        read_only_fields = [
            'id', 'date_creation', 'date_traitement', 'reponse', 'statut'
        ]


class ContactMessageCreateSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour créer un message de contact.
    """
    
    class Meta:
        model = ContactMessage
        fields = ['nom', 'email', 'sujet', 'message']
    
    def validate_email(self, value):
        """Valide l'adresse email."""
        if not value or '@' not in value:
            raise serializers.ValidationError("Adresse email invalide")
        return value


class FAQSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour les questions fréquemment posées.
    """
    
    class Meta:
        model = FAQ
        fields = [
            'id', 'question', 'reponse', 'categorie', 'ordre',
            'actif', 'date_creation', 'date_modification'
        ]
        read_only_fields = ['id', 'date_creation', 'date_modification']


class AppInfoSerializer(serializers.Serializer):
    """
    Sérialiseur pour les informations de l'application.
    """
    
    nom_app = serializers.CharField()
    version = serializers.CharField()
    description = serializers.CharField()
    email_contact = serializers.EmailField()
    telephone_contact = serializers.CharField()
    site_web = serializers.URLField()
    maintenance_mode = serializers.BooleanField()
    inscription_ouverte = serializers.BooleanField()


class AppStatsSerializer(serializers.Serializer):
    """
    Sérialiseur pour les statistiques de l'application.
    """
    
    total_users = serializers.IntegerField()
    total_events = serializers.IntegerField()
    total_transactions = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=10, decimal_places=2)
    active_users_today = serializers.IntegerField()
    events_today = serializers.IntegerField()


class GlobalSearchSerializer(serializers.Serializer):
    """
    Sérialiseur pour la recherche globale.
    """
    
    query = serializers.CharField(max_length=200)
    type = serializers.ChoiceField(
        choices=['all', 'users', 'events'],
        default='all'
    )
    limit = serializers.IntegerField(default=10, max_value=50)
    
    def validate_query(self, value):
        """Valide la requête de recherche."""
        if len(value.strip()) < 2:
            raise serializers.ValidationError(
                "La requête doit contenir au moins 2 caractères"
            )
        return value.strip()


class FileUploadSerializer(serializers.Serializer):
    """
    Sérialiseur pour l'upload de fichiers.
    """
    
    file = serializers.FileField()
    type = serializers.ChoiceField(
        choices=['image', 'document', 'avatar'],
        default='image'
    )
    
    def validate_file(self, value):
        """Valide le fichier uploadé."""
        # Vérifier la taille (10MB max)
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError(
                "Le fichier ne peut pas dépasser 10MB"
            )
        
        # Vérifier le type de fichier
        allowed_types = [
            'image/jpeg', 'image/png', 'image/gif',
            'application/pdf', 'text/plain'
        ]
        
        if value.content_type not in allowed_types:
            raise serializers.ValidationError(
                "Type de fichier non autorisé"
            )
        
        return value


class ReportContentSerializer(serializers.Serializer):
    """
    Sérialiseur pour signaler du contenu.
    """
    
    content_type = serializers.ChoiceField(
        choices=['user', 'event', 'comment']
    )
    content_id = serializers.IntegerField()
    reason = serializers.ChoiceField(choices=[
        'spam', 'inappropriate', 'fake', 'harassment', 'other'
    ])
    description = serializers.CharField(required=False, allow_blank=True)
    
    def validate_content_id(self, value):
        """Valide l'ID du contenu."""
        if value <= 0:
            raise serializers.ValidationError("ID de contenu invalide")
        return value


class HealthCheckSerializer(serializers.Serializer):
    """
    Sérialiseur pour le health check.
    """
    
    status = serializers.CharField()
    timestamp = serializers.DateTimeField()
    version = serializers.CharField()
    database = serializers.CharField()
    cache = serializers.CharField()
    storage = serializers.CharField()


class MaintenanceSerializer(serializers.Serializer):
    """
    Sérialiseur pour le mode maintenance.
    """
    
    maintenance_mode = serializers.BooleanField()
    message = serializers.CharField(required=False, allow_blank=True)
    estimated_duration = serializers.CharField(required=False, allow_blank=True)


class FeedbackSerializer(serializers.Serializer):
    """
    Sérialiseur pour les commentaires/feedback.
    """
    
    rating = serializers.IntegerField(min_value=1, max_value=5)
    comment = serializers.CharField(required=False, allow_blank=True)
    category = serializers.ChoiceField(choices=[
        'app', 'feature', 'bug', 'suggestion'
    ])
    
    def validate_rating(self, value):
        """Valide la note."""
        if not 1 <= value <= 5:
            raise serializers.ValidationError(
                "La note doit être comprise entre 1 et 5"
            )
        return value

