"""
Modèles pour le tableau de bord administrateur.

Ce module définit les modèles spécifiques au dashboard admin :
- AdminAction : Actions effectuées par les administrateurs
- DashboardWidget : Widgets configurables du dashboard
- AdminNotification : Notifications pour les administrateurs
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

User = get_user_model()


class AdminAction(models.Model):
    """
    Modèle pour tracer les actions des administrateurs.
    
    Enregistre toutes les actions importantes effectuées
    par les administrateurs pour l'audit et la traçabilité.
    """
    
    ACTION_CHOICES = [
        ('APPROVE_EVENT', _('Approuver un événement')),
        ('REJECT_EVENT', _('Rejeter un événement')),
        ('APPROVE_USER', _('Approuver un utilisateur')),
        ('REJECT_USER', _('Rejeter un utilisateur')),
        ('SUSPEND_USER', _('Suspendre un utilisateur')),
        ('ACTIVATE_USER', _('Activer un utilisateur')),
        ('PROCESS_REFUND', _('Traiter un remboursement')),
        ('SEND_NOTIFICATION', _('Envoyer une notification')),
        ('UPDATE_SETTINGS', _('Modifier les paramètres')),
        ('EXPORT_DATA', _('Exporter des données')),
        ('DELETE_CONTENT', _('Supprimer du contenu')),
        ('MODERATE_CONTENT', _('Modérer du contenu')),
    ]
    
    admin = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='admin_actions',
        verbose_name=_('Administrateur'),
        help_text="Administrateur qui a effectué l'action"
    )
    
    action = models.CharField(
        _('Action'),
        max_length=30,
        choices=ACTION_CHOICES,
        help_text="Type d'action effectuée"
    )
    
    description = models.TextField(
        _('Description'),
        help_text="Description détaillée de l'action"
    )
    
    # Objet concerné (relation générique)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Type d'objet concerné"
    )
    
    object_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="ID de l'objet concerné"
    )
    
    objet_concerne = GenericForeignKey('content_type', 'object_id')
    
    # Métadonnées
    date_action = models.DateTimeField(
        _('Date de l\'action'),
        auto_now_add=True,
        help_text="Date et heure de l'action"
    )
    
    adresse_ip = models.GenericIPAddressField(
        _('Adresse IP'),
        null=True,
        blank=True,
        help_text="Adresse IP de l'administrateur"
    )
    
    donnees_supplementaires = models.JSONField(
        _('Données supplémentaires'),
        default=dict,
        blank=True,
        help_text="Données supplémentaires sur l'action"
    )
    
    class Meta:
        verbose_name = _('Action administrateur')
        verbose_name_plural = _('Actions administrateur')
        ordering = ['-date_action']
        indexes = [
            models.Index(fields=['admin', 'date_action']),
            models.Index(fields=['action', 'date_action']),
        ]
    
    def __str__(self):
        """Représentation string de l'action."""
        return f"{self.admin.username} - {self.get_action_display()} - {self.date_action.strftime('%d/%m/%Y %H:%M')}"


class DashboardWidget(models.Model):
    """
    Modèle pour les widgets configurables du dashboard.
    
    Permet aux administrateurs de personnaliser leur tableau de bord
    avec des widgets d'information.
    """
    
    TYPE_CHOICES = [
        ('STATS', _('Statistiques')),
        ('CHART', _('Graphique')),
        ('LIST', _('Liste')),
        ('COUNTER', _('Compteur')),
        ('PROGRESS', _('Barre de progression')),
        ('ALERT', _('Alerte')),
    ]
    
    nom = models.CharField(
        _('Nom'),
        max_length=100,
        help_text="Nom du widget"
    )
    
    type_widget = models.CharField(
        _('Type de widget'),
        max_length=20,
        choices=TYPE_CHOICES,
        help_text="Type de widget"
    )
    
    titre = models.CharField(
        _('Titre'),
        max_length=200,
        help_text="Titre affiché sur le widget"
    )
    
    description = models.TextField(
        _('Description'),
        blank=True,
        help_text="Description du widget"
    )
    
    # Configuration
    configuration = models.JSONField(
        _('Configuration'),
        default=dict,
        help_text="Configuration JSON du widget"
    )
    
    requete_sql = models.TextField(
        _('Requête SQL'),
        blank=True,
        help_text="Requête SQL pour récupérer les données"
    )
    
    # Affichage
    largeur = models.PositiveIntegerField(
        _('Largeur'),
        default=6,
        help_text="Largeur du widget (1-12 colonnes Bootstrap)"
    )
    
    hauteur = models.PositiveIntegerField(
        _('Hauteur'),
        default=300,
        help_text="Hauteur du widget en pixels"
    )
    
    ordre = models.PositiveIntegerField(
        _('Ordre d\'affichage'),
        default=0,
        help_text="Ordre d'affichage sur le dashboard"
    )
    
    # Permissions
    visible_pour = models.ManyToManyField(
        User,
        blank=True,
        related_name='dashboard_widgets',
        verbose_name=_('Visible pour'),
        help_text="Utilisateurs pouvant voir ce widget"
    )
    
    # Métadonnées
    actif = models.BooleanField(
        _('Actif'),
        default=True,
        help_text="Widget actif et visible"
    )
    
    date_creation = models.DateTimeField(
        _('Date de création'),
        auto_now_add=True,
        help_text="Date de création du widget"
    )
    
    date_modification = models.DateTimeField(
        _('Date de modification'),
        auto_now=True,
        help_text="Date de dernière modification"
    )
    
    createur = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='widgets_created',
        verbose_name=_('Créateur'),
        help_text="Utilisateur qui a créé ce widget"
    )
    
    class Meta:
        verbose_name = _('Widget de dashboard')
        verbose_name_plural = _('Widgets de dashboard')
        ordering = ['ordre', 'nom']
    
    def __str__(self):
        """Représentation string du widget."""
        return f"{self.nom} ({self.get_type_widget_display()})"


class AdminNotification(models.Model):
    """
    Modèle pour les notifications spécifiques aux administrateurs.
    
    Gère les notifications importantes pour l'équipe d'administration
    comme les alertes système, les demandes de validation, etc.
    """
    
    TYPE_CHOICES = [
        ('VALIDATION_REQUIRED', _('Validation requise')),
        ('SYSTEM_ALERT', _('Alerte système')),
        ('SECURITY_ALERT', _('Alerte sécurité')),
        ('PAYMENT_ISSUE', _('Problème de paiement')),
        ('USER_REPORT', _('Signalement utilisateur')),
        ('TECHNICAL_ISSUE', _('Problème technique')),
        ('MAINTENANCE', _('Maintenance')),
    ]
    
    PRIORITE_CHOICES = [
        ('BASSE', _('Basse')),
        ('NORMALE', _('Normale')),
        ('HAUTE', _('Haute')),
        ('CRITIQUE', _('Critique')),
    ]
    
    STATUT_CHOICES = [
        ('NOUVEAU', _('Nouveau')),
        ('VU', _('Vu')),
        ('EN_COURS', _('En cours')),
        ('RESOLU', _('Résolu')),
        ('IGNORE', _('Ignoré')),
    ]
    
    type_notification = models.CharField(
        _('Type'),
        max_length=30,
        choices=TYPE_CHOICES,
        help_text="Type de notification"
    )
    
    titre = models.CharField(
        _('Titre'),
        max_length=200,
        help_text="Titre de la notification"
    )
    
    message = models.TextField(
        _('Message'),
        help_text="Contenu de la notification"
    )
    
    priorite = models.CharField(
        _('Priorité'),
        max_length=10,
        choices=PRIORITE_CHOICES,
        default='NORMALE',
        help_text="Priorité de la notification"
    )
    
    statut = models.CharField(
        _('Statut'),
        max_length=15,
        choices=STATUT_CHOICES,
        default='NOUVEAU',
        help_text="Statut de la notification"
    )
    
    # Relations
    destinataires = models.ManyToManyField(
        User,
        related_name='admin_notifications',
        verbose_name=_('Destinataires'),
        help_text="Administrateurs destinataires"
    )
    
    # Objet concerné (relation générique)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Type d'objet concerné"
    )
    
    object_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="ID de l'objet concerné"
    )
    
    objet_concerne = GenericForeignKey('content_type', 'object_id')
    
    # Métadonnées
    date_creation = models.DateTimeField(
        _('Date de création'),
        auto_now_add=True,
        help_text="Date de création de la notification"
    )
    
    date_resolution = models.DateTimeField(
        _('Date de résolution'),
        null=True,
        blank=True,
        help_text="Date de résolution de la notification"
    )
    
    lien_action = models.URLField(
        _('Lien d\'action'),
        blank=True,
        help_text="Lien vers l'action à effectuer"
    )
    
    donnees_supplementaires = models.JSONField(
        _('Données supplémentaires'),
        default=dict,
        blank=True,
        help_text="Données supplémentaires"
    )
    
    class Meta:
        verbose_name = _('Notification administrateur')
        verbose_name_plural = _('Notifications administrateur')
        ordering = ['-date_creation']
        indexes = [
            models.Index(fields=['type_notification', 'statut']),
            models.Index(fields=['priorite', 'date_creation']),
        ]
    
    def __str__(self):
        """Représentation string de la notification."""
        return f"{self.titre} - {self.get_priorite_display()}"
    
    def mark_as_resolved(self, admin_user):
        """Marque la notification comme résolue."""
        from django.utils import timezone
        self.statut = 'RESOLU'
        self.date_resolution = timezone.now()
        self.save()
        
        # Enregistrer l'action admin
        AdminAction.objects.create(
            admin=admin_user,
            action='RESOLVE_NOTIFICATION',
            description=f"Résolution de la notification: {self.titre}",
            content_type=ContentType.objects.get_for_model(self),
            object_id=self.id
        )

