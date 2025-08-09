"""
Modèles pour la gestion des abonnements dans SpotVibe.

Ce module définit les modèles pour :
- SubscriptionPlan : Plans d'abonnement disponibles
- Subscription : Abonnements des utilisateurs
- SubscriptionFeature : Fonctionnalités par plan
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class SubscriptionPlan(models.Model):
    """
    Modèle pour les plans d'abonnement.
    
    Définit les différents types d'abonnement disponibles :
    - Standard (10 000 FCFA)
    - Premium (15 000 FCFA)  
    - Gold (20 000 FCFA)
    """
    
    TYPE_CHOICES = [
        ('STANDARD', _('Standard')),
        ('PREMIUM', _('Premium')),
        ('GOLD', _('Gold')),
    ]
    
    DUREE_CHOICES = [
        ('MENSUEL', _('Mensuel')),
        ('TRIMESTRIEL', _('Trimestriel')),
        ('ANNUEL', _('Annuel')),
    ]
    
    nom = models.CharField(
        _('Nom du plan'),
        max_length=50,
        help_text="Nom du plan d'abonnement"
    )
    
    type_plan = models.CharField(
        _('Type de plan'),
        max_length=20,
        choices=TYPE_CHOICES,
        unique=True,
        help_text="Type de plan d'abonnement"
    )
    
    prix = models.DecimalField(
        _('Prix'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Prix de l'abonnement en FCFA"
    )
    
    duree = models.CharField(
        _('Durée'),
        max_length=20,
        choices=DUREE_CHOICES,
        default='MENSUEL',
        help_text="Durée de l'abonnement"
    )
    
    description = models.TextField(
        _('Description'),
        help_text="Description du plan d'abonnement"
    )
    
    # Limites et avantages

    # Métadonnées
    actif = models.BooleanField(
        _('Actif'),
        default=True,
        help_text="Plan disponible à la souscription"
    )
    
    ordre = models.PositiveIntegerField(
        _('Ordre d\'affichage'),
        default=0,
        help_text="Ordre d'affichage dans les listes"
    )
    
    date_creation = models.DateTimeField(
        _('Date de création'),
        auto_now_add=True,
        help_text="Date de création du plan"
    )
    
    date_modification = models.DateTimeField(
        _('Date de modification'),
        auto_now=True,
        help_text="Date de dernière modification"
    )
    
    class Meta:
        verbose_name = _('Plan d\'abonnement')
        verbose_name_plural = _('Plans d\'abonnement')
        ordering = ['ordre', 'prix']
    
    def __str__(self):
        """Représentation string du plan."""
        return f"{self.nom} - {self.prix} FCFA/{self.duree}"
    
    def get_duration_days(self):
        """Retourne la durée en jours."""
        duree_map = {
            'MENSUEL': 30,
            'TRIMESTRIEL': 90,
            'ANNUEL': 365,
        }
        return duree_map.get(self.duree, 30)
    
    def get_subscribers_count(self):
        """Retourne le nombre d'abonnés actifs à ce plan."""
        return self.subscriptions.filter(
            statut='ACTIF',
            date_fin__gt=timezone.now()
        ).count()


class Subscription(models.Model):
    """
    Modèle pour les abonnements des utilisateurs.
    
    Gère les abonnements actifs, leur renouvellement
    et leur historique.
    """
    
    STATUT_CHOICES = [
        ('ACTIF', _('Actif')),
        ('EXPIRE', _('Expiré')),
        ('ANNULE', _('Annulé')),
        ('SUSPENDU', _('Suspendu')),
        ('EN_ATTENTE', _('En attente de paiement')),
    ]
    
    utilisateur = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name=_('Utilisateur'),
        help_text="Utilisateur abonné"
    )
    
    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name=_('Plan'),
        help_text="Plan d'abonnement souscrit"
    )
    
    date_debut = models.DateTimeField(
        _('Date de début'),
        help_text="Date de début de l'abonnement"
    )
    
    date_fin = models.DateTimeField(
        _('Date de fin'),
        help_text="Date de fin de l'abonnement"
    )
    
    statut = models.CharField(
        _('Statut'),
        max_length=20,
        choices=STATUT_CHOICES,
        default='EN_ATTENTE',
        help_text="Statut de l'abonnement"
    )
    
    prix_paye = models.DecimalField(
        _('Prix payé'),
        max_digits=10,
        decimal_places=2,
        help_text="Prix effectivement payé pour cet abonnement"
    )
    
    renouvellement_automatique = models.BooleanField(
        _('Renouvellement automatique'),
        default=True,
        help_text="Renouveler automatiquement l'abonnement"
    )
    
    # Métadonnées
    date_creation = models.DateTimeField(
        _('Date de création'),
        auto_now_add=True,
        help_text="Date de souscription"
    )
    
    date_modification = models.DateTimeField(
        _('Date de modification'),
        auto_now=True,
        help_text="Date de dernière modification"
    )
    
    reference_paiement = models.CharField(
        _('Référence de paiement'),
        max_length=100,
        blank=True,
        help_text="Référence du paiement Mobile Money"
    )
    
    # Utilisation
    evenements_crees_ce_mois = models.PositiveIntegerField(
        _('Événements créés ce mois'),
        default=0,
        help_text="Nombre d'événements créés ce mois"
    )
    
    derniere_reinitialisation_compteur = models.DateTimeField(
        _('Dernière réinitialisation compteur'),
        auto_now_add=True,
        help_text="Dernière réinitialisation du compteur mensuel"
    )
    
    class Meta:
        verbose_name = _('Abonnement')
        verbose_name_plural = _('Abonnements')
        ordering = ['-date_creation']
        indexes = [
            models.Index(fields=['utilisateur', 'statut']),
            models.Index(fields=['date_fin', 'statut']),
        ]
    
    def __str__(self):
        """Représentation string de l'abonnement."""
        return f"{self.utilisateur.username} - {self.plan.nom} ({self.statut})"
    
    def save(self, *args, **kwargs):
        """Sauvegarde avec calcul automatique de la date de fin."""
        if not self.date_fin and self.date_debut:
            duration_days = self.plan.get_duration_days()
            self.date_fin = self.date_debut + timedelta(days=duration_days)
        
        # Mettre à jour le statut si expiré
        if self.date_fin < timezone.now() and self.statut == 'ACTIF':
            self.statut = 'EXPIRE'
        
        super().save(*args, **kwargs)
    
    def is_active(self):
        """Vérifie si l'abonnement est actif."""
        return (
            self.statut == 'ACTIF' and
            self.date_fin > timezone.now()
        )
    
    def days_remaining(self):
        """Retourne le nombre de jours restants."""
        if not self.is_active():
            return 0
        
        delta = self.date_fin - timezone.now()
        return max(0, delta.days)
    
    def can_create_event(self):
        """Vérifie si l'utilisateur peut créer un événement selon son plan et ses fonctionnalités."""
        if not self.is_active():
            return False
        
        self.reset_monthly_counter_if_needed()
        
        # Récupérer la limite d'événements depuis les fonctionnalités du plan
        try:
            event_limit_feature = self.plan.features.get(nom='max_evenements_par_mois')
            max_events = int(event_limit_feature.limite) if event_limit_feature.limite.isdigit() else None
        except SubscriptionFeature.DoesNotExist:
            max_events = None # Ou une valeur par défaut si la fonctionnalité n'existe pas

        if max_events is None:
            return True  # Illimité si la fonctionnalité n'est pas définie ou non numérique
        
        return self.evenements_crees_ce_mois < max_events
    
    def increment_events_counter(self):
        """Incrémente le compteur d'événements créés ce mois."""
        self.reset_monthly_counter_if_needed()
        self.evenements_crees_ce_mois += 1
        self.save(update_fields=['evenements_crees_ce_mois'])
    
    def reset_monthly_counter_if_needed(self):
        """Réinitialise le compteur mensuel si nécessaire."""
        now = timezone.now()
        last_reset = self.derniere_reinitialisation_compteur
        
        # Réinitialiser si on est dans un nouveau mois
        if (now.year != last_reset.year or 
            now.month != last_reset.month):
            self.evenements_crees_ce_mois = 0
            self.derniere_reinitialisation_compteur = now
            self.save(update_fields=[
                'evenements_crees_ce_mois',
                'derniere_reinitialisation_compteur'
            ])
    
    def get_commission_rate(self):
        """Retourne le taux de commission applicable selon le plan et ses fonctionnalités."""
        if not self.is_active():
            from django.conf import settings
            return getattr(settings, 'DEFAULT_TICKET_COMMISSION_RATE', 10) # Taux par défaut si pas d'abonnement actif

        try:
            commission_feature = self.plan.features.get(nom='commission_reduite')
            return float(commission_feature.limite) # La limite contient le taux de commission
        except SubscriptionFeature.DoesNotExist:
            from django.conf import settings
            return getattr(settings, 'DEFAULT_TICKET_COMMISSION_RATE', 10) # Taux par défaut si la fonctionnalité n\'existe pas
        
class SubscriptionFeature(models.Model):
    """
    Modèle pour les fonctionnalités des plans d'abonnement.
    
    Permet de définir de manière flexible les fonctionnalités
    incluses dans chaque plan.
    """
    
    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.CASCADE,
        related_name='features',
        verbose_name=_('Plan'),
        help_text="Plan d'abonnement"
    )
    
    nom = models.CharField(
        _('Nom de la fonctionnalité'),
        max_length=100,
        help_text="Nom de la fonctionnalité"
    )
    
    description = models.TextField(
        _('Description'),
        help_text="Description détaillée de la fonctionnalité"
    )
    
    inclus = models.BooleanField(
        _('Inclus'),
        default=True,
        help_text="Fonctionnalité incluse dans ce plan"
    )
    
    limite = models.CharField(
        _('Limite'),
        max_length=50,
        blank=True,
        help_text="Limite de la fonctionnalité (ex: '10 par mois', 'Illimité')"
    )
    
    ordre = models.PositiveIntegerField(
        _('Ordre d\'affichage'),
        default=0,
        help_text="Ordre d'affichage dans les listes"
    )
    
    class Meta:
        verbose_name = _('Fonctionnalité d\'abonnement')
        verbose_name_plural = _('Fonctionnalités d\'abonnement')
        ordering = ['plan', 'ordre', 'nom']
        unique_together = ['plan', 'nom']
    
    def __str__(self):
        """Représentation string de la fonctionnalité."""
        status = "✓" if self.inclus else "✗"
        return f"{self.plan.nom} - {self.nom} {status}"


class SubscriptionHistory(models.Model):
    """
    Modèle pour l'historique des abonnements.
    
    Conserve un historique de tous les changements d'abonnement
    pour les statistiques et la facturation.
    """
    
    ACTION_CHOICES = [
        ('SOUSCRIPTION', _('Souscription')),
        ('RENOUVELLEMENT', _('Renouvellement')),
        ('CHANGEMENT_PLAN', _('Changement de plan')),
        ('ANNULATION', _('Annulation')),
        ('SUSPENSION', _('Suspension')),
        ('REACTIVATION', _('Réactivation')),
    ]
    
    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.CASCADE,
        related_name='history',
        verbose_name=_('Abonnement'),
        help_text="Abonnement concerné"
    )
    
    action = models.CharField(
        _('Action'),
        max_length=20,
        choices=ACTION_CHOICES,
        help_text="Type d'action effectuée"
    )
    
    ancien_statut = models.CharField(
        _('Ancien statut'),
        max_length=20,
        blank=True,
        help_text="Statut avant l'action"
    )
    
    nouveau_statut = models.CharField(
        _('Nouveau statut'),
        max_length=20,
        help_text="Statut après l'action"
    )
    
    commentaire = models.TextField(
        _('Commentaire'),
        blank=True,
        help_text="Commentaire sur l'action"
    )
    
    date_action = models.DateTimeField(
        _('Date de l\'action'),
        auto_now_add=True,
        help_text="Date de l'action"
    )
    
    utilisateur_action = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subscription_actions',
        verbose_name=_('Utilisateur de l\'action'),
        help_text="Utilisateur qui a effectué l'action (admin)"
    )
    
    class Meta:
        verbose_name = _('Historique d\'abonnement')
        verbose_name_plural = _('Historiques d\'abonnement')
        ordering = ['-date_action']
    
    def __str__(self):
        """Représentation string de l'historique."""
        return f"{self.subscription.utilisateur.username} - {self.action} ({self.date_action.strftime('%d/%m/%Y')})"

