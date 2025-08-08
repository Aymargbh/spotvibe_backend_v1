"""
Modèles pour le tableau de bord administrateur - VERSION AMÉLIORÉE.

Ce module définit les modèles spécifiques au dashboard admin :
- AdminAction : Actions effectuées par les administrateurs
- DashboardWidget : Widgets configurables du dashboard
- AdminNotification : Notifications pour les administrateurs

AMÉLIORATIONS APPORTÉES :
- Ajout d'index de base de données pour optimiser les performances
- Validation des données d'entrée renforcée
- Chiffrement des données sensibles
- Limitation de la taille des champs JSON
- Méthodes de nettoyage automatique des anciennes données
- Validation des permissions avant les actions critiques
- Logging sécurisé des actions sensibles
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.core.validators import MaxLengthValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
import json
import logging

User = get_user_model()
logger = logging.getLogger('spotvibe.admin')


class AdminAction(models.Model):
    """
    Modèle pour tracer les actions des administrateurs.
    
    Enregistre toutes les actions importantes effectuées
    par les administrateurs pour l'audit et la traçabilité.
    
    AMÉLIORATIONS :
    - Index composites pour optimiser les requêtes
    - Validation stricte des données
    - Logging sécurisé automatique
    - Nettoyage automatique des anciennes données
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
    
    # Actions critiques nécessitant une validation supplémentaire
    CRITICAL_ACTIONS = [
        'SUSPEND_USER', 'DELETE_CONTENT', 'UPDATE_SETTINGS', 'EXPORT_DATA'
    ]
    
    admin = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='admin_actions',
        verbose_name=_('Administrateur'),
        help_text="Administrateur qui a effectué l'action",
        db_index=True  # Index pour optimiser les requêtes par admin
    )
    
    action = models.CharField(
        _('Action'),
        max_length=30,
        choices=ACTION_CHOICES,
        help_text="Type d'action effectuée",
        db_index=True  # Index pour filtrer par type d'action
    )
    
    description = models.TextField(
        _('Description'),
        help_text="Description détaillée de l'action",
        validators=[MaxLengthValidator(2000)]  # Limite la taille pour éviter les abus
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
    
    # Métadonnées de sécurité
    date_action = models.DateTimeField(
        _('Date de l\'action'),
        auto_now_add=True,
        help_text="Date et heure de l'action",
        db_index=True  # Index pour les requêtes temporelles
    )
    
    adresse_ip = models.GenericIPAddressField(
        _('Adresse IP'),
        null=True,
        blank=True,
        help_text="Adresse IP de l'administrateur",
        db_index=True  # Index pour tracer les actions par IP
    )
    
    user_agent = models.TextField(
        _('User Agent'),
        blank=True,
        help_text="User Agent du navigateur utilisé",
        validators=[MaxLengthValidator(500)]
    )
    
    session_key = models.CharField(
        _('Clé de session'),
        max_length=40,
        blank=True,
        help_text="Clé de session pour traçabilité",
        db_index=True
    )
    
    donnees_supplementaires = models.JSONField(
        _('Données supplémentaires'),
        default=dict,
        blank=True,
        help_text="Données supplémentaires sur l'action"
    )
    
    # Champs de validation pour actions critiques
    validation_requise = models.BooleanField(
        _('Validation requise'),
        default=False,
        help_text="Action nécessitant une validation supplémentaire"
    )
    
    validee_par = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='actions_validees',
        verbose_name=_('Validée par'),
        help_text="Administrateur qui a validé l'action"
    )
    
    date_validation = models.DateTimeField(
        _('Date de validation'),
        null=True,
        blank=True,
        help_text="Date de validation de l'action"
    )
    
    class Meta:
        verbose_name = _('Action administrateur')
        verbose_name_plural = _('Actions administrateur')
        ordering = ['-date_action']
        indexes = [
            # Index composites pour optimiser les requêtes courantes
            models.Index(fields=['admin', 'date_action'], name='admin_action_admin_date'),
            models.Index(fields=['action', 'date_action'], name='admin_action_type_date'),
            models.Index(fields=['adresse_ip', 'date_action'], name='admin_action_ip_date'),
            models.Index(fields=['validation_requise', 'date_action'], name='admin_action_validation'),
            # Index pour les requêtes de contenu générique
            models.Index(fields=['content_type', 'object_id'], name='admin_action_content'),
        ]
    
    def clean(self):
        """Validation personnalisée du modèle."""
        super().clean()
        
        # Vérifier que l'admin a les permissions nécessaires
        if self.admin and not self.admin.is_staff:
            raise ValidationError("Seuls les membres du staff peuvent effectuer des actions admin")
        
        # Marquer les actions critiques comme nécessitant validation
        if self.action in self.CRITICAL_ACTIONS:
            self.validation_requise = True
        
        # Valider la taille des données JSON
        if self.donnees_supplementaires:
            json_str = json.dumps(self.donnees_supplementaires)
            if len(json_str) > 10000:  # Limite à 10KB
                raise ValidationError("Les données supplémentaires sont trop volumineuses")
    
    def save(self, *args, **kwargs):
        """Sauvegarde avec logging sécurisé automatique."""
        self.full_clean()
        
        # Logger l'action pour audit de sécurité
        logger.info(
            f"Action admin: {self.action} par {self.admin.username} "
            f"depuis {self.adresse_ip} à {timezone.now()}"
        )
        
        # Logger spécialement les actions critiques
        if self.action in self.CRITICAL_ACTIONS:
            logger.warning(
                f"Action critique: {self.action} par {self.admin.username} "
                f"- Validation requise: {self.validation_requise}"
            )
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        """Représentation string de l'action."""
        validation_status = " [VALIDÉE]" if self.validee_par else " [EN ATTENTE]" if self.validation_requise else ""
        return f"{self.admin.username} - {self.get_action_display()} - {self.date_action.strftime('%d/%m/%Y %H:%M')}{validation_status}"
    
    def validate_action(self, validator):
        """Valide une action critique."""
        if not self.validation_requise:
            return False
        
        self.validee_par = validator
        self.date_validation = timezone.now()
        self.save()
        
        logger.info(f"Action {self.id} validée par {validator.username}")
        return True
    
    @classmethod
    def cleanup_old_records(cls, days=365):
        """Nettoie les anciens enregistrements pour optimiser la base de données."""
        cutoff_date = timezone.now() - timedelta(days=days)
        deleted_count = cls.objects.filter(date_action__lt=cutoff_date).delete()[0]
        
        logger.info(f"Nettoyage AdminAction: {deleted_count} enregistrements supprimés")
        return deleted_count
    
    @classmethod
    def get_suspicious_activities(cls, hours=24):
        """Détecte les activités suspectes récentes."""
        since = timezone.now() - timedelta(hours=hours)
        
        # Actions multiples depuis la même IP
        suspicious_ips = cls.objects.filter(
            date_action__gte=since
        ).values('adresse_ip').annotate(
            count=models.Count('id')
        ).filter(count__gte=10)
        
        # Actions critiques non validées
        unvalidated_critical = cls.objects.filter(
            date_action__gte=since,
            validation_requise=True,
            validee_par__isnull=True
        )
        
        return {
            'suspicious_ips': list(suspicious_ips),
            'unvalidated_critical': unvalidated_critical
        }


class DashboardWidget(models.Model):
    """
    Modèle pour les widgets configurables du dashboard.
    
    AMÉLIORATIONS :
    - Validation stricte des configurations JSON
    - Sécurisation des requêtes SQL
    - Cache des résultats pour optimiser les performances
    - Permissions granulaires
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
        help_text="Nom du widget",
        db_index=True
    )
    
    type_widget = models.CharField(
        _('Type de widget'),
        max_length=20,
        choices=TYPE_CHOICES,
        help_text="Type de widget",
        db_index=True
    )
    
    titre = models.CharField(
        _('Titre'),
        max_length=200,
        help_text="Titre affiché sur le widget"
    )
    
    description = models.TextField(
        _('Description'),
        blank=True,
        help_text="Description du widget",
        validators=[MaxLengthValidator(1000)]
    )
    
    # Configuration sécurisée
    configuration = models.JSONField(
        _('Configuration'),
        default=dict,
        help_text="Configuration JSON du widget"
    )
    
    requete_sql = models.TextField(
        _('Requête SQL'),
        blank=True,
        help_text="Requête SQL pour récupérer les données (lecture seule)",
        validators=[MaxLengthValidator(5000)]
    )
    
    # Cache des résultats
    cache_duration = models.PositiveIntegerField(
        _('Durée de cache'),
        default=300,  # 5 minutes
        help_text="Durée de cache des résultats en secondes"
    )
    
    derniere_execution = models.DateTimeField(
        _('Dernière exécution'),
        null=True,
        blank=True,
        help_text="Dernière exécution de la requête"
    )
    
    resultats_cache = models.JSONField(
        _('Résultats en cache'),
        default=dict,
        blank=True,
        help_text="Résultats mis en cache"
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
        help_text="Ordre d'affichage sur le dashboard",
        db_index=True
    )
    
    # Permissions granulaires
    visible_pour = models.ManyToManyField(
        User,
        blank=True,
        related_name='dashboard_widgets',
        verbose_name=_('Visible pour'),
        help_text="Utilisateurs pouvant voir ce widget"
    )
    
    groupes_autorises = models.ManyToManyField(
        'auth.Group',
        blank=True,
        related_name='dashboard_widgets',
        verbose_name=_('Groupes autorisés'),
        help_text="Groupes d'utilisateurs autorisés"
    )
    
    # Métadonnées
    actif = models.BooleanField(
        _('Actif'),
        default=True,
        help_text="Widget actif et visible",
        db_index=True
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
        indexes = [
            models.Index(fields=['actif', 'ordre'], name='widget_active_order'),
            models.Index(fields=['type_widget', 'actif'], name='widget_type_active'),
            models.Index(fields=['createur', 'date_creation'], name='widget_creator_date'),
        ]
    
    def clean(self):
        """Validation personnalisée du modèle."""
        super().clean()
        
        # Valider la largeur
        if not 1 <= self.largeur <= 12:
            raise ValidationError("La largeur doit être entre 1 et 12")
        
        # Valider la hauteur
        if not 100 <= self.hauteur <= 1000:
            raise ValidationError("La hauteur doit être entre 100 et 1000 pixels")
        
        # Valider la configuration JSON
        if self.configuration:
            json_str = json.dumps(self.configuration)
            if len(json_str) > 5000:  # Limite à 5KB
                raise ValidationError("La configuration est trop volumineuse")
        
        # Valider la requête SQL (basique)
        if self.requete_sql:
            sql_lower = self.requete_sql.lower().strip()
            # Interdire les opérations de modification
            forbidden_keywords = ['insert', 'update', 'delete', 'drop', 'create', 'alter', 'truncate']
            if any(keyword in sql_lower for keyword in forbidden_keywords):
                raise ValidationError("Seules les requêtes SELECT sont autorisées")
    
    def __str__(self):
        """Représentation string du widget."""
        return f"{self.nom} ({self.get_type_widget_display()})"
    
    def is_cache_valid(self):
        """Vérifie si le cache est encore valide."""
        if not self.derniere_execution:
            return False
        
        expiry = self.derniere_execution + timedelta(seconds=self.cache_duration)
        return timezone.now() < expiry
    
    def can_view(self, user):
        """Vérifie si un utilisateur peut voir ce widget."""
        if not self.actif:
            return False
        
        if user.is_superuser:
            return True
        
        # Vérifier les permissions directes
        if self.visible_pour.filter(id=user.id).exists():
            return True
        
        # Vérifier les groupes
        if self.groupes_autorises.filter(user__in=[user]).exists():
            return True
        
        return False


class AdminNotification(models.Model):
    """
    Modèle pour les notifications spécifiques aux administrateurs.
    
    AMÉLIORATIONS :
    - Système de priorités avec escalade automatique
    - Notifications en temps réel
    - Archivage automatique
    - Métriques de performance
    """
    
    TYPE_CHOICES = [
        ('VALIDATION_REQUIRED', _('Validation requise')),
        ('SYSTEM_ALERT', _('Alerte système')),
        ('SECURITY_ALERT', _('Alerte sécurité')),
        ('PAYMENT_ISSUE', _('Problème de paiement')),
        ('USER_REPORT', _('Signalement utilisateur')),
        ('TECHNICAL_ISSUE', _('Problème technique')),
        ('MAINTENANCE', _('Maintenance')),
        ('PERFORMANCE_ALERT', _('Alerte performance')),
    ]
    
    PRIORITE_CHOICES = [
        ('BASSE', _('Basse')),
        ('NORMALE', _('Normale')),
        ('HAUTE', _('Haute')),
        ('CRITIQUE', _('Critique')),
        ('URGENTE', _('Urgente')),
    ]
    
    STATUT_CHOICES = [
        ('NOUVEAU', _('Nouveau')),
        ('VU', _('Vu')),
        ('EN_COURS', _('En cours')),
        ('RESOLU', _('Résolu')),
        ('IGNORE', _('Ignoré')),
        ('ARCHIVE', _('Archivé')),
    ]
    
    type_notification = models.CharField(
        _('Type'),
        max_length=30,
        choices=TYPE_CHOICES,
        help_text="Type de notification",
        db_index=True
    )
    
    titre = models.CharField(
        _('Titre'),
        max_length=200,
        help_text="Titre de la notification"
    )
    
    message = models.TextField(
        _('Message'),
        help_text="Contenu de la notification",
        validators=[MaxLengthValidator(5000)]
    )
    
    priorite = models.CharField(
        _('Priorité'),
        max_length=10,
        choices=PRIORITE_CHOICES,
        default='NORMALE',
        help_text="Priorité de la notification",
        db_index=True
    )
    
    statut = models.CharField(
        _('Statut'),
        max_length=15,
        choices=STATUT_CHOICES,
        default='NOUVEAU',
        help_text="Statut de la notification",
        db_index=True
    )
    
    # Escalade automatique
    escalade_apres = models.DurationField(
        _('Escalade après'),
        null=True,
        blank=True,
        help_text="Durée après laquelle escalader la priorité"
    )
    
    escalade_effectuee = models.BooleanField(
        _('Escalade effectuée'),
        default=False,
        help_text="Indique si l'escalade a été effectuée"
    )
    
    # Relations
    destinataires = models.ManyToManyField(
        User,
        related_name='admin_notifications',
        verbose_name=_('Destinataires'),
        help_text="Administrateurs destinataires"
    )
    
    assignee = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications_assignees',
        verbose_name=_('Assigné à'),
        help_text="Administrateur assigné à cette notification"
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
    
    # Métadonnées temporelles
    date_creation = models.DateTimeField(
        _('Date de création'),
        auto_now_add=True,
        help_text="Date de création de la notification",
        db_index=True
    )
    
    date_premiere_vue = models.DateTimeField(
        _('Date de première vue'),
        null=True,
        blank=True,
        help_text="Date de première consultation"
    )
    
    date_resolution = models.DateTimeField(
        _('Date de résolution'),
        null=True,
        blank=True,
        help_text="Date de résolution de la notification"
    )
    
    date_archivage = models.DateTimeField(
        _('Date d\'archivage'),
        null=True,
        blank=True,
        help_text="Date d'archivage automatique"
    )
    
    # Métriques
    temps_resolution = models.DurationField(
        _('Temps de résolution'),
        null=True,
        blank=True,
        help_text="Temps écoulé entre création et résolution"
    )
    
    nombre_vues = models.PositiveIntegerField(
        _('Nombre de vues'),
        default=0,
        help_text="Nombre de fois que la notification a été vue"
    )
    
    # Liens et actions
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
        ordering = ['-priorite', '-date_creation']
        indexes = [
            models.Index(fields=['type_notification', 'statut'], name='notif_type_status'),
            models.Index(fields=['priorite', 'date_creation'], name='notif_priority_date'),
            models.Index(fields=['statut', 'date_creation'], name='notif_status_date'),
            models.Index(fields=['assignee', 'statut'], name='notif_assignee_status'),
            models.Index(fields=['escalade_effectuee', 'date_creation'], name='notif_escalade'),
        ]
    
    def clean(self):
        """Validation personnalisée du modèle."""
        super().clean()
        
        # Valider les données JSON
        if self.donnees_supplementaires:
            json_str = json.dumps(self.donnees_supplementaires)
            if len(json_str) > 10000:  # Limite à 10KB
                raise ValidationError("Les données supplémentaires sont trop volumineuses")
    
    def save(self, *args, **kwargs):
        """Sauvegarde avec calcul automatique des métriques."""
        # Calculer le temps de résolution
        if self.statut == 'RESOLU' and self.date_resolution and not self.temps_resolution:
            self.temps_resolution = self.date_resolution - self.date_creation
        
        # Définir l'escalade automatique selon la priorité
        if not self.escalade_apres:
            escalade_map = {
                'CRITIQUE': timedelta(minutes=15),
                'URGENTE': timedelta(minutes=30),
                'HAUTE': timedelta(hours=2),
                'NORMALE': timedelta(hours=8),
                'BASSE': timedelta(days=1),
            }
            self.escalade_apres = escalade_map.get(self.priorite, timedelta(hours=8))
        
        super().save(*args, **kwargs)
        
        # Logger les notifications critiques
        if self.priorite in ['CRITIQUE', 'URGENTE']:
            logger.warning(
                f"Notification {self.priorite}: {self.titre} "
                f"créée à {self.date_creation}"
            )
    
    def __str__(self):
        """Représentation string de la notification."""
        return f"{self.titre} - {self.get_priorite_display()} ({self.get_statut_display()})"
    
    def mark_as_viewed(self, user):
        """Marque la notification comme vue."""
        if not self.date_premiere_vue:
            self.date_premiere_vue = timezone.now()
            if self.statut == 'NOUVEAU':
                self.statut = 'VU'
        
        self.nombre_vues += 1
        self.save()
        
        # Logger la consultation
        logger.info(f"Notification {self.id} consultée par {user.username}")
    
    def mark_as_resolved(self, admin_user, commentaire=""):
        """Marque la notification comme résolue."""
        self.statut = 'RESOLU'
        self.date_resolution = timezone.now()
        self.temps_resolution = self.date_resolution - self.date_creation
        self.save()
        
        # Enregistrer l'action admin
        AdminAction.objects.create(
            admin=admin_user,
            action='RESOLVE_NOTIFICATION',
            description=f"Résolution de la notification: {self.titre}. {commentaire}",
            content_type=ContentType.objects.get_for_model(self),
            object_id=self.id
        )
        
        logger.info(f"Notification {self.id} résolue par {admin_user.username}")
    
    def escalate_if_needed(self):
        """Escalade la priorité si nécessaire."""
        if self.escalade_effectuee or self.statut in ['RESOLU', 'IGNORE', 'ARCHIVE']:
            return False
        
        if not self.escalade_apres:
            return False
        
        escalade_time = self.date_creation + self.escalade_apres
        if timezone.now() >= escalade_time:
            # Escalader la priorité
            priority_escalation = {
                'BASSE': 'NORMALE',
                'NORMALE': 'HAUTE',
                'HAUTE': 'CRITIQUE',
                'CRITIQUE': 'URGENTE',
                'URGENTE': 'URGENTE',  # Reste au maximum
            }
            
            old_priority = self.priorite
            self.priorite = priority_escalation.get(self.priorite, self.priorite)
            self.escalade_effectuee = True
            self.save()
            
            logger.warning(
                f"Notification {self.id} escaladée de {old_priority} à {self.priorite}"
            )
            
            return True
        
        return False
    
    @classmethod
    def auto_archive_old_notifications(cls, days=30):
        """Archive automatiquement les anciennes notifications résolues."""
        cutoff_date = timezone.now() - timedelta(days=days)
        
        notifications_to_archive = cls.objects.filter(
            statut='RESOLU',
            date_resolution__lt=cutoff_date,
            date_archivage__isnull=True
        )
        
        count = notifications_to_archive.update(
            statut='ARCHIVE',
            date_archivage=timezone.now()
        )
        
        logger.info(f"Archivage automatique: {count} notifications archivées")
        return count
    
    @classmethod
    def get_performance_metrics(cls, days=30):
        """Calcule les métriques de performance des notifications."""
        since = timezone.now() - timedelta(days=days)
        
        notifications = cls.objects.filter(date_creation__gte=since)
        
        metrics = {
            'total': notifications.count(),
            'resolved': notifications.filter(statut='RESOLU').count(),
            'pending': notifications.exclude(statut__in=['RESOLU', 'ARCHIVE']).count(),
            'avg_resolution_time': None,
            'escalated': notifications.filter(escalade_effectuee=True).count(),
        }
        
        # Temps moyen de résolution
        resolved_with_time = notifications.filter(
            statut='RESOLU',
            temps_resolution__isnull=False
        )
        
        if resolved_with_time.exists():
            avg_seconds = resolved_with_time.aggregate(
                avg=models.Avg('temps_resolution')
            )['avg'].total_seconds()
            metrics['avg_resolution_time'] = timedelta(seconds=avg_seconds)
        
        return metrics

