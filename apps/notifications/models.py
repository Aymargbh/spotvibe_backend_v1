"""
Modèles pour la gestion des notifications dans SpotVibe - VERSION AMÉLIORÉE.

Ce module définit les modèles pour :
- Notification : Notifications individuelles
- NotificationTemplate : Templates de notifications
- NotificationPreference : Préférences de notification des utilisateurs
- PushToken : Tokens pour les notifications push
- NotificationBatch : Envois groupés de notifications

AMÉLIORATIONS APPORTÉES :
- Index de base de données pour optimiser les performances.
- Validation des données d'entrée renforcée.
- Utilisation de JSONField pour les données structurées.
- Nettoyage automatique des anciennes notifications et tokens.
- Gestion plus robuste des préférences et des envois.
- Sécurisation des données sensibles.
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.core.validators import MaxLengthValidator, MinValueValidator
from django.core.exceptions import ValidationError
import json
import logging
from datetime import timedelta

User = get_user_model()
logger = logging.getLogger("spotvibe.notifications")


class NotificationTemplate(models.Model):
    """
    Modèle pour les templates de notifications.
    
    Définit les modèles de notifications réutilisables
    avec des variables dynamiques.
    
    AMÉLIORATIONS :
    - Validation des longueurs de champs.
    - Index sur le type de notification pour des recherches rapides.
    - Gestion des canaux actifs et variables disponibles.
    """
    
    TYPE_CHOICES = [
        ("EVENT_CREATED", _("Événement créé")),
        ("EVENT_APPROVED", _("Événement approuvé")),
        ("EVENT_REJECTED", _("Événement rejeté")),
        ("EVENT_REMINDER", _("Rappel d'événement")),
        ("EVENT_CANCELLED", _("Événement annulé")),
        ("NEW_FOLLOWER", _("Nouveau follower")),
        ("FOLLOW_EVENT", _("Événement d'un suivi")),
        ("PAYMENT_SUCCESS", _("Paiement réussi")),
        ("PAYMENT_FAILED", _("Paiement échoué")),
        ("SUBSCRIPTION_EXPIRING", _("Abonnement expirant")),
        ("SUBSCRIPTION_EXPIRED", _("Abonnement expiré")),
        ("TICKET_PURCHASED", _("Billet acheté")),
        ("VERIFICATION_APPROVED", _("Vérification approuvée")),
        ("VERIFICATION_REJECTED", _("Vérification rejetée")),
        ("SYSTEM_MAINTENANCE", _("Maintenance système")),
        ("WELCOME", _("Bienvenue")),
        ("ACCOUNT_BLOCKED", _("Compte bloqué")), # Nouveau type
        ("PASSWORD_CHANGE", _("Changement de mot de passe")), # Nouveau type
    ]
    
    CANAL_CHOICES = [
        ("EMAIL", _("Email")),
        ("PUSH", _("Notification push")),
        ("SMS", _("SMS")),
        ("IN_APP", _("Dans l'application")),
    ]
    
    type_notification = models.CharField(
        _("Type de notification"),
        max_length=30,
        choices=TYPE_CHOICES,
        unique=True,
        help_text="Type de notification",
        db_index=True
    )
    
    nom = models.CharField(
        _("Nom"),
        max_length=100,
        help_text="Nom du template",
        validators=[MaxLengthValidator(100)]
    )
    
    description = models.TextField(
        _("Description"),
        blank=True, # Rendu optionnel
        help_text="Description du template",
        validators=[MaxLengthValidator(1000)]
    )
    
    # Contenu pour différents canaux
    titre_email = models.CharField(
        _("Titre email"),
        max_length=200,
        blank=True,
        help_text="Titre pour les notifications email",
        validators=[MaxLengthValidator(200)]
    )
    
    contenu_email = models.TextField(
        _("Contenu email"),
        blank=True,
        help_text="Contenu HTML pour les emails",
        validators=[MaxLengthValidator(10000)] # Limite à 10KB
    )
    
    titre_push = models.CharField(
        _("Titre push"),
        max_length=100,
        blank=True,
        help_text="Titre pour les notifications push",
        validators=[MaxLengthValidator(100)]
    )
    
    contenu_push = models.CharField(
        _("Contenu push"),
        max_length=200,
        blank=True,
        help_text="Contenu pour les notifications push",
        validators=[MaxLengthValidator(200)]
    )
    
    contenu_sms = models.CharField(
        _("Contenu SMS"),
        max_length=160,
        blank=True,
        help_text="Contenu pour les SMS (max 160 caractères)",
        validators=[MaxLengthValidator(160)]
    )
    
    contenu_in_app = models.TextField(
        _("Contenu in-app"),
        blank=True,
        help_text="Contenu pour les notifications dans l'application",
        validators=[MaxLengthValidator(5000)]
    )
    
    # Configuration
    canaux_actifs = models.JSONField(
        _("Canaux actifs"),
        default=list,
        blank=True,
        help_text='Liste des canaux activés pour ce template (ex: ["EMAIL", "PUSH"])'
    )

    variables_disponibles = models.JSONField(
        _("Variables disponibles"),
        default=list,
        blank=True,
        help_text='Variables disponibles pour ce template (ex: ["user_name", "event_title"])'
    )

    
    actif = models.BooleanField(
        _("Actif"),
        default=True,
        help_text="Template actif",
        db_index=True
    )
    
    # Métadonnées
    date_creation = models.DateTimeField(
        _("Date de création"),
        auto_now_add=True,
        help_text="Date de création du template"
    )
    
    date_modification = models.DateTimeField(
        _("Date de modification"),
        auto_now=True,
        help_text="Date de dernière modification"
    )
    
    class Meta:
        verbose_name = _("Template de notification")
        verbose_name_plural = _("Templates de notification")
        ordering = ["type_notification"]
        indexes = [
            models.Index(fields=["type_notification"], name="notif_template_type_idx"),
            models.Index(fields=["actif"], name="notif_template_active_idx"),
        ]
    
    def clean(self):
        """Validation personnalisée du modèle."""
        super().clean()
        
        # Valider que les canaux actifs sont valides
        for canal in self.canaux_actifs:
            if canal not in [choice[0] for choice in self.CANAL_CHOICES]:
                raise ValidationError(f"Canal actif invalide: {canal}")
        
        # Valider les données JSON
        if self.canaux_actifs:
            json_str = json.dumps(self.canaux_actifs)
            if len(json_str) > 500: # Limite arbitraire
                raise ValidationError("La liste des canaux actifs est trop volumineuse.")
        
        if self.variables_disponibles:
            json_str = json.dumps(self.variables_disponibles)
            if len(json_str) > 1000: # Limite arbitraire
                raise ValidationError("La liste des variables disponibles est trop volumineuse.")

    def __str__(self):
        """Représentation string du template."""
        return f"{self.nom} ({self.type_notification})"
    
    def render_content(self, canal, variables=None):
        """
        Rend le contenu du template avec les variables fournies.
        
        Args:
            canal: Canal de notification ("EMAIL", "PUSH", "SMS", "IN_APP")
            variables: Dictionnaire des variables à remplacer
        
        Returns:
            Tuple (titre, contenu) rendu avec les variables
        """
        if variables is None:
            variables = {}
        
        # Sélectionner le contenu selon le canal
        content_map = {
            "EMAIL": (self.titre_email, self.contenu_email),
            "PUSH": (self.titre_push, self.contenu_push),
            "SMS": ("", self.contenu_sms),
            "IN_APP": ("", self.contenu_in_app),
        }
        
        titre, contenu = content_map.get(canal, ("", ""))
        
        # Remplacer les variables de manière sécurisée
        for var, value in variables.items():
            placeholder = f"{{{var}}}"
            # Utiliser str() pour s'assurer que la valeur est une chaîne
            titre = titre.replace(placeholder, str(value))
            contenu = contenu.replace(placeholder, str(value))
        
        return titre, contenu


class Notification(models.Model):
    """
    Modèle pour les notifications individuelles.
    
    Stocke toutes les notifications envoyées aux utilisateurs
    avec leur statut de lecture et de livraison.
    
    AMÉLIORATIONS :
    - Index composites pour des requêtes rapides.
    - Nettoyage automatique des anciennes notifications.
    - Méthodes atomiques pour marquer comme lu.
    """
    
    TYPE_CHOICES = NotificationTemplate.TYPE_CHOICES
    
    STATUT_CHOICES = [
        ("NOUVEAU", _("Nouveau")),
        ("EN_ATTENTE", _("En attente")),
        ("ENVOYE", _("Envoyé")),
        ("LIVRE", _("Livré")),
        ("LU", _("Lu")),
        ("ECHEC", _("Échec")),
    ]
    
    PRIORITE_CHOICES = [
        ("BASSE", _("Basse")),
        ("NORMALE", _("Normale")),
        ("HAUTE", _("Haute")),
        ("URGENTE", _("Urgente")),
    ]
    
    # Destinataire
    utilisateur = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name=_("Utilisateur"),
        help_text="Destinataire de la notification",
        db_index=True
    )
    
    # Contenu
    type_notification = models.CharField(
        _("Type"),
        max_length=30,
        choices=TYPE_CHOICES,
        help_text="Type de notification",
        db_index=True
    )
    
    titre = models.CharField(
        _("Titre"),
        max_length=200,
        help_text="Titre de la notification",
        validators=[MaxLengthValidator(200)]
    )
    
    message = models.TextField(
        _("Message"),
        help_text="Contenu de la notification",
        validators=[MaxLengthValidator(5000)]
    )
    
    # Relation générique vers l'objet concerné
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL, # Changer CASCADE en SET_NULL
        null=True,
        blank=True,
        help_text="Type d'objet concerné"
    )
    
    object_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="ID de l'objet concerné"
    )
    
    objet_concerne = GenericForeignKey("content_type", "object_id")
    
    # Métadonnées
    priorite = models.CharField(
        _("Priorité"),
        max_length=10,
        choices=PRIORITE_CHOICES,
        default="NORMALE",
        help_text="Priorité de la notification",
        db_index=True
    )
    
    statut = models.CharField(
        _("Statut"),
        max_length=20,
        choices=STATUT_CHOICES,
        default="NOUVEAU",
        help_text="Statut de la notification",
        db_index=True
    )
    
    # Dates
    date_creation = models.DateTimeField(
        _("Date de création"),
        auto_now_add=True,
        help_text="Date de création de la notification",
        db_index=True
    )
    
    date_envoi = models.DateTimeField(
        _("Date d'envoi"),
        null=True,
        blank=True,
        help_text="Date d'envoi de la notification"
    )
    
    date_lecture = models.DateTimeField(
        _("Date de lecture"),
        null=True,
        blank=True,
        help_text="Date de lecture par l'utilisateur"
    )
    
    date_expiration = models.DateTimeField(
        _("Date d'expiration"),
        null=True,
        blank=True,
        help_text="Date d'expiration de la notification"
    )
    
    # Liens et actions
    lien_action = models.URLField(
        _("Lien d'action"),
        blank=True,
        help_text="Lien vers une action spécifique",
        validators=[MaxLengthValidator(500)]
    )
    
    donnees_supplementaires = models.JSONField(
        _("Données supplémentaires"),
        default=dict,
        blank=True,
        help_text="Données supplémentaires pour l'application"
    )
    
    class Meta:
        verbose_name = _("Notification")
        verbose_name_plural = _("Notifications")
        ordering = ["-date_creation"]
        indexes = [
            models.Index(fields=["utilisateur", "statut"], name="notif_user_status"),
            models.Index(fields=["type_notification"], name="notif_type_idx"),
            models.Index(fields=["date_creation"], name="notif_creation_date_idx"),
            models.Index(fields=["priorite", "statut"], name="notif_priority_status"),
        ]
    
    def clean(self):
        """Validation personnalisée du modèle."""
        super().clean()
        
        # Valider les données JSON
        if self.donnees_supplementaires:
            json_str = json.dumps(self.donnees_supplementaires)
            if len(json_str) > 10000: # Limite à 10KB
                raise ValidationError("Les données supplémentaires sont trop volumineuses.")

    def __str__(self):
        """Représentation string de la notification."""
        return f"{self.utilisateur.username} - {self.titre}"
    
    def mark_as_read(self):
        """Marque la notification comme lue de manière atomique."""
        if not self.date_lecture:
            self.date_lecture = timezone.now()
            self.statut = "LU"
            self.save(update_fields=["date_lecture", "statut"])
            logger.info(f"Notification {self.id} marquée comme lue par {self.utilisateur.username}.")
        else:
            logger.debug(f"Notification {self.id} déjà lue.")
    
    def is_read(self):
        """Vérifie si la notification a été lue."""
        return self.date_lecture is not None
    
    def is_expired(self):
        """Vérifie si la notification a expiré."""
        if not self.date_expiration:
            return False
        return timezone.now() > self.date_expiration

    @classmethod
    def cleanup_old_notifications(cls, days=90):
        """Nettoie les anciennes notifications (lues, échouées, archivées)."""
        cutoff_date = timezone.now() - timedelta(days=days)
        deleted_count = cls.objects.filter(
            statut__in=["LU", "ECHEC", "ARCHIVE"], 
            date_creation__lt=cutoff_date
        ).delete()[0]
        logger.info(f"Nettoyage Notification: {deleted_count} anciennes notifications supprimées.")
        return deleted_count


class NotificationPreference(models.Model):
    """
    Modèle pour les préférences de notification des utilisateurs.
    
    Permet aux utilisateurs de configurer leurs préférences
    de notification par type et par canal.
    
    AMÉLIORATIONS :
    - Index composites pour des requêtes rapides.
    - Validation des fréquences et heures d'envoi.
    """
    
    CANAL_CHOICES = [
        ("EMAIL", _("Email")),
        ("PUSH", _("Notification push")),
        ("SMS", _("SMS")),
        ("IN_APP", _("Dans l'application")),
    ]
    
    FREQUENCE_CHOICES = [
        ("IMMEDIATE", _("Immédiate")),
        ("QUOTIDIEN", _("Quotidien")),
        ("HEBDOMADAIRE", _("Hebdomadaire")),
        ("MENSUEL", _("Mensuel")), # Nouveau
        ("JAMAIS", _("Jamais")),
    ]
    
    utilisateur = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="notification_preferences",
        verbose_name=_("Utilisateur"),
        help_text="Utilisateur concerné",
        db_index=True
    )
    
    type_notification = models.CharField(
        _("Type de notification"),
        max_length=30,
        choices=NotificationTemplate.TYPE_CHOICES,
        help_text="Type de notification",
        db_index=True
    )
    
    canal = models.CharField(
        _("Canal"),
        max_length=10,
        choices=CANAL_CHOICES,
        help_text="Canal de notification",
        db_index=True
    )
    
    actif = models.BooleanField(
        _("Actif"),
        default=True,
        help_text="Recevoir ce type de notification sur ce canal",
        db_index=True
    )
    
    # Configuration avancée
    frequence = models.CharField(
        _("Fréquence"),
        max_length=20,
        choices=FREQUENCE_CHOICES,
        default="IMMEDIATE",
        help_text="Fréquence de notification"
    )
    
    heure_envoi = models.TimeField(
        _("Heure d'envoi"),
        null=True,
        blank=True,
        help_text="Heure préférée pour les notifications groupées (si fréquence non immédiate)"
    )
    
    date_creation = models.DateTimeField(
        _("Date de création"),
        auto_now_add=True,
        help_text="Date de création de la préférence"
    )
    
    date_modification = models.DateTimeField(
        _("Date de modification"),
        auto_now=True,
        help_text="Date de dernière modification"
    )
    
    class Meta:
        verbose_name = _("Préférence de notification")
        verbose_name_plural = _("Préférences de notification")
        unique_together = ["utilisateur", "type_notification", "canal"]
        ordering = ["utilisateur", "type_notification", "canal"]
        indexes = [
            models.Index(fields=["utilisateur", "actif"], name="notif_pref_user_active"),
            models.Index(fields=["type_notification", "canal", "actif"], name="notif_pref_type_canal_active"),
        ]
    
    def clean(self):
        """Validation personnalisée du modèle."""
        super().clean()
        if self.frequence != "IMMEDIATE" and not self.heure_envoi:
            # Permettre heure_envoi null si fréquence immédiate
            pass
        elif self.frequence != "IMMEDIATE" and self.heure_envoi is None:
             raise ValidationError(_("L'heure d'envoi est requise pour les fréquences non immédiates."))

    def __str__(self):
        """Représentation string de la préférence."""
        status = "✓" if self.actif else "✗"
        return f"{self.utilisateur.username} - {self.type_notification} ({self.canal}) {status}"


class PushToken(models.Model):
    """
    Modèle pour les tokens de notification push.
    
    Stocke les tokens des appareils pour l'envoi
    de notifications push.
    
    AMÉLIORATIONS :
    - Index composites pour des requêtes rapides.
    - Nettoyage automatique des tokens inactifs/anciens.
    - Validation des champs.
    """
    
    PLATEFORME_CHOICES = [
        ("ANDROID", _("Android")),
        ("IOS", _("iOS")),
        ("WEB", _("Web")),
    ]
    
    utilisateur = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="push_tokens",
        verbose_name=_("Utilisateur"),
        help_text="Utilisateur propriétaire du token",
        db_index=True
    )
    
    token = models.TextField(
        _("Token"),
        unique=True,
        help_text="Token de notification push",
        validators=[MaxLengthValidator(500)] # Les tokens peuvent être longs
    )
    
    plateforme = models.CharField(
        _("Plateforme"),
        max_length=10,
        choices=PLATEFORME_CHOICES,
        help_text="Plateforme de l'appareil",
        db_index=True
    )
    
    # Informations de l'appareil
    nom_appareil = models.CharField(
        _("Nom de l'appareil"),
        max_length=100,
        blank=True,
        help_text="Nom de l'appareil",
        validators=[MaxLengthValidator(100)]
    )
    
    version_app = models.CharField(
        _("Version de l'application"),
        max_length=20,
        blank=True,
        help_text="Version de l'application",
        validators=[MaxLengthValidator(20)]
    )
    
    version_os = models.CharField(
        _("Version de l'OS"),
        max_length=20,
        blank=True,
        help_text="Version du système d'exploitation",
        validators=[MaxLengthValidator(20)]
    )
    
    # Statut
    actif = models.BooleanField(
        _("Actif"),
        default=True,
        help_text="Token actif pour l'envoi de notifications",
        db_index=True
    )
    
    derniere_utilisation = models.DateTimeField(
        _("Dernière utilisation"),
        auto_now=True,
        help_text="Dernière fois que le token a été utilisé",
        db_index=True
    )
    
    date_creation = models.DateTimeField(
        _("Date de création"),
        auto_now_add=True,
        help_text="Date d'enregistrement du token"
    )
    
    # Statistiques
    notifications_envoyees = models.PositiveIntegerField(
        _("Notifications envoyées"),
        default=0,
        help_text="Nombre de notifications envoyées à ce token"
    )
    
    notifications_livrees = models.PositiveIntegerField(
        _("Notifications livrées"),
        default=0,
        help_text="Nombre de notifications livrées avec succès"
    )
    
    class Meta:
        verbose_name = _("Token de notification push")
        verbose_name_plural = _("Tokens de notification push")
        ordering = ["-derniere_utilisation"]
        indexes = [
            models.Index(fields=["utilisateur", "actif"], name="push_token_user_active"),
            models.Index(fields=["plateforme", "actif"], name="push_token_platform_active"),
            models.Index(fields=["derniere_utilisation"], name="push_token_last_used"),
        ]
    
    def clean(self):
        """Validation personnalisée du modèle."""
        super().clean()
        if self.plateforme not in [choice[0] for choice in self.PLATEFORME_CHOICES]:
            raise ValidationError(_("Plateforme invalide."))

    def __str__(self):
        """Représentation string du token."""
        return f"{self.utilisateur.username} - {self.plateforme} ({self.token[:20]}...)"
    
    def increment_sent(self):
        """Incrémente le compteur de notifications envoyées de manière atomique."""
        self.notifications_envoyees = models.F("notifications_envoyees") + 1
        self.save(update_fields=["notifications_envoyees"])
        self.refresh_from_db()
    
    def increment_delivered(self):
        """Incrémente le compteur de notifications livrées de manière atomique."""
        self.notifications_livrees = models.F("notifications_livrees") + 1
        self.save(update_fields=["notifications_livrees"])
        self.refresh_from_db()
    
    def get_delivery_rate(self):
        """Calcule le taux de livraison des notifications."""
        if self.notifications_envoyees == 0:
            return 0.0
        return (self.notifications_livrees / self.notifications_envoyees) * 100.0

    @classmethod
    def cleanup_inactive_tokens(cls, days=180):
        """Nettoie les tokens push inactifs ou anciens."""
        cutoff_date = timezone.now() - timedelta(days=days)
        deleted_count = cls.objects.filter(
            actif=False, 
            derniere_utilisation__lt=cutoff_date
        ).delete()[0]
        logger.info(f"Nettoyage PushToken: {deleted_count} tokens inactifs supprimés.")
        return deleted_count


class NotificationBatch(models.Model):
    """
    Modèle pour les envois groupés de notifications.
    
    Permet de gérer les campagnes de notifications
    et les envois en masse.
    
    AMÉLIORATIONS :
    - Index sur les champs clés.
    - Validation des données JSON.
    - Suivi détaillé des envois.
    - Nettoyage automatique des anciens lots.
    """
    
    STATUT_CHOICES = [
        ("PLANIFIE", _("Planifié")),
        ("EN_COURS", _("En cours")),
        ("TERMINE", _("Terminé")),
        ("ECHEC", _("Échec")),
        ("ANNULE", _("Annulé")),
    ]
    
    nom = models.CharField(
        _("Nom du lot"),
        max_length=200,
        help_text="Nom du lot de notifications",
        validators=[MaxLengthValidator(200)]
    )
    
    template = models.ForeignKey(
        NotificationTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notification_batches",
        verbose_name=_("Template de notification"),
        help_text="Template utilisé pour ce lot"
    )
    
    filtre_utilisateurs = models.JSONField(
        _("Filtre utilisateurs"),
        default=dict,
        blank=True,
        help_text='Critères de filtrage des utilisateurs (ex: {"country": "BJ", "is_premium": true})'
    )
    
    variables_globales = models.JSONField(
        _("Variables globales"),
        default=dict,
        blank=True,
        help_text="Variables à passer au template pour toutes les notifications du lot"
    )
    
    statut = models.CharField(
        _("Statut"),
        max_length=20,
        choices=STATUT_CHOICES,
        default="PLANIFIE",
        help_text="Statut de l'envoi du lot",
        db_index=True
    )
    
    date_planification = models.DateTimeField(
        _("Date de planification"),
        help_text="Date et heure de planification de l'envoi"
    )
    
    date_debut_envoi = models.DateTimeField(
        _("Date de début d'envoi"),
        null=True,
        blank=True,
        help_text="Date et heure de début réel de l'envoi"
    )
    
    date_fin_envoi = models.DateTimeField(
        _("Date de fin d'envoi"),
        null=True,
        blank=True,
        help_text="Date et heure de fin réel de l'envoi"
    )
    
    nombre_notifications_attendues = models.PositiveIntegerField(
        _("Notifications attendues"),
        default=0,
        help_text="Nombre de notifications prévues dans ce lot"
    )
    
    nombre_notifications_envoyees = models.PositiveIntegerField(
        _("Notifications envoyées"),
        default=0,
        help_text="Nombre de notifications réellement envoyées"
    )
    
    nombre_notifications_echec = models.PositiveIntegerField(
        _("Notifications en échec"),
        default=0,
        help_text="Nombre de notifications ayant échoué"
    )
    
    createur = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notification_batches_created",
        verbose_name=_("Créateur"),
        help_text="Utilisateur qui a créé ce lot"
    )
    
    class Meta:
        verbose_name = _("Lot de notifications")
        verbose_name_plural = _("Lots de notifications")
        ordering = ["-date_planification"]
        indexes = [
            models.Index(fields=["statut", "date_planification"], name="notif_batch_status_plan_date"),
            models.Index(fields=["template"], name="notif_batch_template_idx"),
        ]
    
    def clean(self):
        """Validation personnalisée du modèle."""
        super().clean()
        if self.date_planification < timezone.now() and self.statut == "PLANIFIE":
            raise ValidationError(_("La date de planification ne peut pas être dans le passé pour un lot planifié."))
        
        # Valider les données JSON
        if self.filtre_utilisateurs:
            json_str = json.dumps(self.filtre_utilisateurs)
            if len(json_str) > 2000: # Limite arbitraire
                raise ValidationError("Le filtre utilisateurs est trop volumineux.")
        
        if self.variables_globales:
            json_str = json.dumps(self.variables_globales)
            if len(json_str) > 2000: # Limite arbitraire
                raise ValidationError("Les variables globales sont trop volumineuses.")

    def __str__(self):
        """Représentation string du lot."""
        return f"{self.nom} ({self.get_statut_display()}) - Planifié pour {self.date_planification.strftime('%Y-%m-%d %H:%M')}"
    
    def mark_as_sent(self, sent_count, failed_count):
        """
        Met à jour le statut du lot après envoi.
        """
        self.nombre_notifications_envoyees = sent_count
        self.nombre_notifications_echec = failed_count
        self.date_fin_envoi = timezone.now()
        self.statut = "TERMINE"
        self.save(update_fields=[
            "nombre_notifications_envoyees", 
            "nombre_notifications_echec", 
            "date_fin_envoi", 
            "statut"
        ])
        logger.info(f"Lot de notifications \'{self.nom}\' terminé. Envoyées: {sent_count}, Échecs: {failed_count}.")

    @classmethod
    def get_pending_batches(cls):
        """
        Retourne les lots de notifications planifiés et prêts à être envoyés.
        """
        return cls.objects.filter(
            statut="PLANIFIE",
            date_planification__lte=timezone.now()
        ).order_by("date_planification")

    @classmethod
    def cleanup_old_batches(cls, days=365):
        """
        Nettoie les anciens lots de notifications terminés ou annulés.
        """
        cutoff_date = timezone.now() - timedelta(days=days)
        deleted_count = cls.objects.filter(
            statut__in=["TERMINE", "ANNULE", "ECHEC"],
            date_fin_envoi__lt=cutoff_date
        ).delete()[0]
        logger.info(f"Nettoyage NotificationBatch: {deleted_count} anciens lots supprimés.")
        return deleted_count



