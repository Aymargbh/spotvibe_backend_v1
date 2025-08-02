"""
Modèles pour la gestion des notifications dans SpotVibe.

Ce module définit les modèles pour :
- Notification : Notifications individuelles
- NotificationTemplate : Templates de notifications
- NotificationPreference : Préférences de notification des utilisateurs
- PushToken : Tokens pour les notifications push
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

User = get_user_model()


class NotificationTemplate(models.Model):
    """
    Modèle pour les templates de notifications.
    
    Définit les modèles de notifications réutilisables
    avec des variables dynamiques.
    """
    
    TYPE_CHOICES = [
        ('EVENT_CREATED', _('Événement créé')),
        ('EVENT_APPROVED', _('Événement approuvé')),
        ('EVENT_REJECTED', _('Événement rejeté')),
        ('EVENT_REMINDER', _('Rappel d\'événement')),
        ('EVENT_CANCELLED', _('Événement annulé')),
        ('NEW_FOLLOWER', _('Nouveau follower')),
        ('FOLLOW_EVENT', _('Événement d\'un suivi')),
        ('PAYMENT_SUCCESS', _('Paiement réussi')),
        ('PAYMENT_FAILED', _('Paiement échoué')),
        ('SUBSCRIPTION_EXPIRING', _('Abonnement expirant')),
        ('SUBSCRIPTION_EXPIRED', _('Abonnement expiré')),
        ('TICKET_PURCHASED', _('Billet acheté')),
        ('VERIFICATION_APPROVED', _('Vérification approuvée')),
        ('VERIFICATION_REJECTED', _('Vérification rejetée')),
        ('SYSTEM_MAINTENANCE', _('Maintenance système')),
        ('WELCOME', _('Bienvenue')),
    ]
    
    CANAL_CHOICES = [
        ('EMAIL', _('Email')),
        ('PUSH', _('Notification push')),
        ('SMS', _('SMS')),
        ('IN_APP', _('Dans l\'application')),
    ]
    
    type_notification = models.CharField(
        _('Type de notification'),
        max_length=30,
        choices=TYPE_CHOICES,
        unique=True,
        help_text="Type de notification"
    )
    
    nom = models.CharField(
        _('Nom'),
        max_length=100,
        help_text="Nom du template"
    )
    
    description = models.TextField(
        _('Description'),
        help_text="Description du template"
    )
    
    # Contenu pour différents canaux
    titre_email = models.CharField(
        _('Titre email'),
        max_length=200,
        blank=True,
        help_text="Titre pour les notifications email"
    )
    
    contenu_email = models.TextField(
        _('Contenu email'),
        blank=True,
        help_text="Contenu HTML pour les emails"
    )
    
    titre_push = models.CharField(
        _('Titre push'),
        max_length=100,
        blank=True,
        help_text="Titre pour les notifications push"
    )
    
    contenu_push = models.CharField(
        _('Contenu push'),
        max_length=200,
        blank=True,
        help_text="Contenu pour les notifications push"
    )
    
    contenu_sms = models.CharField(
        _('Contenu SMS'),
        max_length=160,
        blank=True,
        help_text="Contenu pour les SMS (max 160 caractères)"
    )
    
    contenu_in_app = models.TextField(
        _('Contenu in-app'),
        blank=True,
        help_text="Contenu pour les notifications dans l'application"
    )
    
    # Configuration
    canaux_actifs = models.JSONField(
        _('Canaux actifs'),
        default=list,
        help_text="Liste des canaux activés pour ce template"
    )
    
    variables_disponibles = models.JSONField(
        _('Variables disponibles'),
        default=list,
        help_text="Variables disponibles pour ce template (ex: {user_name}, {event_title})"
    )
    
    actif = models.BooleanField(
        _('Actif'),
        default=True,
        help_text="Template actif"
    )
    
    # Métadonnées
    date_creation = models.DateTimeField(
        _('Date de création'),
        auto_now_add=True,
        help_text="Date de création du template"
    )
    
    date_modification = models.DateTimeField(
        _('Date de modification'),
        auto_now=True,
        help_text="Date de dernière modification"
    )
    
    class Meta:
        verbose_name = _('Template de notification')
        verbose_name_plural = _('Templates de notification')
        ordering = ['type_notification']
    
    def __str__(self):
        """Représentation string du template."""
        return f"{self.nom} ({self.type_notification})"
    
    def render_content(self, canal, variables=None):
        """
        Rend le contenu du template avec les variables fournies.
        
        Args:
            canal: Canal de notification ('EMAIL', 'PUSH', 'SMS', 'IN_APP')
            variables: Dictionnaire des variables à remplacer
        
        Returns:
            Tuple (titre, contenu) rendu avec les variables
        """
        if variables is None:
            variables = {}
        
        # Sélectionner le contenu selon le canal
        content_map = {
            'EMAIL': (self.titre_email, self.contenu_email),
            'PUSH': (self.titre_push, self.contenu_push),
            'SMS': ('', self.contenu_sms),
            'IN_APP': ('', self.contenu_in_app),
        }
        
        titre, contenu = content_map.get(canal, ('', ''))
        
        # Remplacer les variables
        for var, value in variables.items():
            placeholder = f"{{{var}}}"
            titre = titre.replace(placeholder, str(value))
            contenu = contenu.replace(placeholder, str(value))
        
        return titre, contenu


class Notification(models.Model):
    """
    Modèle pour les notifications individuelles.
    
    Stocke toutes les notifications envoyées aux utilisateurs
    avec leur statut de lecture et de livraison.
    """
    
    TYPE_CHOICES = NotificationTemplate.TYPE_CHOICES
    
    STATUT_CHOICES = [
        ('EN_ATTENTE', _('En attente')),
        ('ENVOYE', _('Envoyé')),
        ('LIVRE', _('Livré')),
        ('LU', _('Lu')),
        ('ECHEC', _('Échec')),
    ]
    
    PRIORITE_CHOICES = [
        ('BASSE', _('Basse')),
        ('NORMALE', _('Normale')),
        ('HAUTE', _('Haute')),
        ('URGENTE', _('Urgente')),
    ]
    
    # Destinataire
    utilisateur = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name=_('Utilisateur'),
        help_text="Destinataire de la notification"
    )
    
    # Contenu
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
    
    # Relation générique vers l'objet concerné
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
    priorite = models.CharField(
        _('Priorité'),
        max_length=10,
        choices=PRIORITE_CHOICES,
        default='NORMALE',
        help_text="Priorité de la notification"
    )
    
    statut = models.CharField(
        _('Statut'),
        max_length=20,
        choices=STATUT_CHOICES,
        default='EN_ATTENTE',
        help_text="Statut de la notification"
    )
    
    # Dates
    date_creation = models.DateTimeField(
        _('Date de création'),
        auto_now_add=True,
        help_text="Date de création de la notification"
    )
    
    date_envoi = models.DateTimeField(
        _('Date d\'envoi'),
        null=True,
        blank=True,
        help_text="Date d'envoi de la notification"
    )
    
    date_lecture = models.DateTimeField(
        _('Date de lecture'),
        null=True,
        blank=True,
        help_text="Date de lecture par l'utilisateur"
    )
    
    date_expiration = models.DateTimeField(
        _('Date d\'expiration'),
        null=True,
        blank=True,
        help_text="Date d'expiration de la notification"
    )
    
    # Liens et actions
    lien_action = models.URLField(
        _('Lien d\'action'),
        blank=True,
        help_text="Lien vers une action spécifique"
    )
    
    donnees_supplementaires = models.JSONField(
        _('Données supplémentaires'),
        default=dict,
        blank=True,
        help_text="Données supplémentaires pour l'application"
    )
    
    class Meta:
        verbose_name = _('Notification')
        verbose_name_plural = _('Notifications')
        ordering = ['-date_creation']
        indexes = [
            models.Index(fields=['utilisateur', 'statut']),
            models.Index(fields=['type_notification']),
            models.Index(fields=['date_creation']),
        ]
    
    def __str__(self):
        """Représentation string de la notification."""
        return f"{self.utilisateur.username} - {self.titre}"
    
    def mark_as_read(self):
        """Marque la notification comme lue."""
        if not self.date_lecture:
            self.date_lecture = timezone.now()
            self.statut = 'LU'
            self.save(update_fields=['date_lecture', 'statut'])
    
    def is_read(self):
        """Vérifie si la notification a été lue."""
        return self.date_lecture is not None
    
    def is_expired(self):
        """Vérifie si la notification a expiré."""
        if not self.date_expiration:
            return False
        return timezone.now() > self.date_expiration


class NotificationPreference(models.Model):
    """
    Modèle pour les préférences de notification des utilisateurs.
    
    Permet aux utilisateurs de configurer leurs préférences
    de notification par type et par canal.
    """
    
    CANAL_CHOICES = [
        ('EMAIL', _('Email')),
        ('PUSH', _('Notification push')),
        ('SMS', _('SMS')),
        ('IN_APP', _('Dans l\'application')),
    ]
    
    utilisateur = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notification_preferences',
        verbose_name=_('Utilisateur'),
        help_text="Utilisateur concerné"
    )
    
    type_notification = models.CharField(
        _('Type de notification'),
        max_length=30,
        choices=NotificationTemplate.TYPE_CHOICES,
        help_text="Type de notification"
    )
    
    canal = models.CharField(
        _('Canal'),
        max_length=10,
        choices=CANAL_CHOICES,
        help_text="Canal de notification"
    )
    
    actif = models.BooleanField(
        _('Actif'),
        default=True,
        help_text="Recevoir ce type de notification sur ce canal"
    )
    
    # Configuration avancée
    frequence = models.CharField(
        _('Fréquence'),
        max_length=20,
        choices=[
            ('IMMEDIATE', _('Immédiate')),
            ('QUOTIDIEN', _('Quotidien')),
            ('HEBDOMADAIRE', _('Hebdomadaire')),
            ('JAMAIS', _('Jamais')),
        ],
        default='IMMEDIATE',
        help_text="Fréquence de notification"
    )
    
    heure_envoi = models.TimeField(
        _('Heure d\'envoi'),
        null=True,
        blank=True,
        help_text="Heure préférée pour les notifications groupées"
    )
    
    date_creation = models.DateTimeField(
        _('Date de création'),
        auto_now_add=True,
        help_text="Date de création de la préférence"
    )
    
    date_modification = models.DateTimeField(
        _('Date de modification'),
        auto_now=True,
        help_text="Date de dernière modification"
    )
    
    class Meta:
        verbose_name = _('Préférence de notification')
        verbose_name_plural = _('Préférences de notification')
        unique_together = ['utilisateur', 'type_notification', 'canal']
        ordering = ['utilisateur', 'type_notification', 'canal']
    
    def __str__(self):
        """Représentation string de la préférence."""
        status = "✓" if self.actif else "✗"
        return f"{self.utilisateur.username} - {self.type_notification} ({self.canal}) {status}"


class PushToken(models.Model):
    """
    Modèle pour les tokens de notification push.
    
    Stocke les tokens des appareils pour l'envoi
    de notifications push.
    """
    
    PLATEFORME_CHOICES = [
        ('ANDROID', _('Android')),
        ('IOS', _('iOS')),
        ('WEB', _('Web')),
    ]
    
    utilisateur = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='push_tokens',
        verbose_name=_('Utilisateur'),
        help_text="Utilisateur propriétaire du token"
    )
    
    token = models.TextField(
        _('Token'),
        unique=True,
        help_text="Token de notification push"
    )
    
    plateforme = models.CharField(
        _('Plateforme'),
        max_length=10,
        choices=PLATEFORME_CHOICES,
        help_text="Plateforme de l'appareil"
    )
    
    # Informations de l'appareil
    nom_appareil = models.CharField(
        _('Nom de l\'appareil'),
        max_length=100,
        blank=True,
        help_text="Nom de l'appareil"
    )
    
    version_app = models.CharField(
        _('Version de l\'application'),
        max_length=20,
        blank=True,
        help_text="Version de l'application"
    )
    
    version_os = models.CharField(
        _('Version de l\'OS'),
        max_length=20,
        blank=True,
        help_text="Version du système d'exploitation"
    )
    
    # Statut
    actif = models.BooleanField(
        _('Actif'),
        default=True,
        help_text="Token actif pour l'envoi de notifications"
    )
    
    derniere_utilisation = models.DateTimeField(
        _('Dernière utilisation'),
        auto_now=True,
        help_text="Dernière fois que le token a été utilisé"
    )
    
    date_creation = models.DateTimeField(
        _('Date de création'),
        auto_now_add=True,
        help_text="Date d'enregistrement du token"
    )
    
    # Statistiques
    notifications_envoyees = models.PositiveIntegerField(
        _('Notifications envoyées'),
        default=0,
        help_text="Nombre de notifications envoyées à ce token"
    )
    
    notifications_livrees = models.PositiveIntegerField(
        _('Notifications livrées'),
        default=0,
        help_text="Nombre de notifications livrées avec succès"
    )
    
    class Meta:
        verbose_name = _('Token de notification push')
        verbose_name_plural = _('Tokens de notification push')
        ordering = ['-derniere_utilisation']
        indexes = [
            models.Index(fields=['utilisateur', 'actif']),
            models.Index(fields=['plateforme', 'actif']),
        ]
    
    def __str__(self):
        """Représentation string du token."""
        return f"{self.utilisateur.username} - {self.plateforme} ({self.token[:20]}...)"
    
    def increment_sent(self):
        """Incrémente le compteur de notifications envoyées."""
        self.notifications_envoyees += 1
        self.save(update_fields=['notifications_envoyees'])
    
    def increment_delivered(self):
        """Incrémente le compteur de notifications livrées."""
        self.notifications_livrees += 1
        self.save(update_fields=['notifications_livrees'])
    
    def get_delivery_rate(self):
        """Calcule le taux de livraison des notifications."""
        if self.notifications_envoyees == 0:
            return 0
        return (self.notifications_livrees / self.notifications_envoyees) * 100


class NotificationBatch(models.Model):
    """
    Modèle pour les envois groupés de notifications.
    
    Permet de gérer les campagnes de notifications
    et les envois en masse.
    """
    
    STATUT_CHOICES = [
        ('PLANIFIE', _('Planifié')),
        ('EN_COURS', _('En cours')),
        ('TERMINE', _('Terminé')),
        ('ECHEC', _('Échec')),
        ('ANNULE', _('Annulé')),
    ]
    
    nom = models.CharField(
        _('Nom'),
        max_length=100,
        help_text="Nom de la campagne"
    )
    
    description = models.TextField(
        _('Description'),
        blank=True,
        help_text="Description de la campagne"
    )
    
    template = models.ForeignKey(
        NotificationTemplate,
        on_delete=models.CASCADE,
        related_name='batches',
        verbose_name=_('Template'),
        help_text="Template utilisé pour cette campagne"
    )
    
    # Ciblage
    destinataires = models.ManyToManyField(
        User,
        related_name='notification_batches',
        verbose_name=_('Destinataires'),
        help_text="Utilisateurs ciblés par cette campagne"
    )
    
    criteres_ciblage = models.JSONField(
        _('Critères de ciblage'),
        default=dict,
        blank=True,
        help_text="Critères de sélection des destinataires"
    )
    
    # Planification
    date_planifiee = models.DateTimeField(
        _('Date planifiée'),
        help_text="Date et heure d'envoi planifiée"
    )
    
    statut = models.CharField(
        _('Statut'),
        max_length=20,
        choices=STATUT_CHOICES,
        default='PLANIFIE',
        help_text="Statut de la campagne"
    )
    
    # Résultats
    nombre_destinataires = models.PositiveIntegerField(
        _('Nombre de destinataires'),
        default=0,
        help_text="Nombre total de destinataires"
    )
    
    nombre_envoyes = models.PositiveIntegerField(
        _('Nombre envoyés'),
        default=0,
        help_text="Nombre de notifications envoyées"
    )
    
    nombre_livres = models.PositiveIntegerField(
        _('Nombre livrés'),
        default=0,
        help_text="Nombre de notifications livrées"
    )
    
    nombre_lus = models.PositiveIntegerField(
        _('Nombre lus'),
        default=0,
        help_text="Nombre de notifications lues"
    )
    
    # Métadonnées
    date_creation = models.DateTimeField(
        _('Date de création'),
        auto_now_add=True,
        help_text="Date de création de la campagne"
    )
    
    date_debut_envoi = models.DateTimeField(
        _('Date de début d\'envoi'),
        null=True,
        blank=True,
        help_text="Date de début d'envoi effectif"
    )
    
    date_fin_envoi = models.DateTimeField(
        _('Date de fin d\'envoi'),
        null=True,
        blank=True,
        help_text="Date de fin d'envoi"
    )
    
    createur = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notification_batches_created',
        verbose_name=_('Créateur'),
        help_text="Utilisateur qui a créé cette campagne"
    )
    
    class Meta:
        verbose_name = _('Campagne de notification')
        verbose_name_plural = _('Campagnes de notification')
        ordering = ['-date_creation']
    
    def __str__(self):
        """Représentation string de la campagne."""
        return f"{self.nom} - {self.statut}"
    
    def get_delivery_rate(self):
        """Calcule le taux de livraison."""
        if self.nombre_envoyes == 0:
            return 0
        return (self.nombre_livres / self.nombre_envoyes) * 100
    
    def get_read_rate(self):
        """Calcule le taux de lecture."""
        if self.nombre_livres == 0:
            return 0
        return (self.nombre_lus / self.nombre_livres) * 100

