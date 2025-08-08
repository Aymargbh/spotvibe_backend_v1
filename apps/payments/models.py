"""
Modèles pour la gestion des paiements dans SpotVibe.

Ce module définit les modèles pour :
- Payment : Paiements effectués sur la plateforme
- MomoTransaction : Transactions Mobile Money
- Commission : Commissions perçues par la plateforme
- Refund : Remboursements
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
import uuid

from apps.events.models import EventTicket

User = get_user_model()


class Payment(models.Model):
    """
    Modèle principal pour tous les paiements sur la plateforme.
    
    Centralise tous les types de paiements :
    - Abonnements
    - Billets d'événements
    - Commissions
    """
    
    TYPE_CHOICES = [
        ('ABONNEMENT', _('Abonnement')),
        ('BILLET', _('Billet d\'événement')),
        ('COMMISSION', _('Commission')),
        ('REMBOURSEMENT', _('Remboursement')),
    ]
    
    STATUT_CHOICES = [
        ('EN_ATTENTE', _('En attente')),
        ('EN_COURS', _('En cours')),
        ('REUSSI', _('Réussi')),
        ('ECHEC', _('Échec')),
        ('ANNULE', _('Annulé')),
        ('REMBOURSE', _('Remboursé')),
    ]
    
    METHODE_CHOICES = [
        ('MOMO_MTN', _('Mobile Money MTN')),
        ('MOMO_MOOV', _('Mobile Money Moov')),
        ('CARTE_BANCAIRE', _('Carte bancaire')),
        ('VIREMENT', _('Virement bancaire')),
        ('ESPECES', _('Espèces')),
    ]
    
    # Identifiant unique
    uuid = models.UUIDField(
        _('Identifiant unique'),
        default=uuid.uuid4,
        editable=False,
        unique=True,
        help_text="Identifiant unique du paiement"
    )
    
    # Relations
    utilisateur = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name=_('Utilisateur'),
        help_text="Utilisateur qui effectue le paiement"
    )
    
    # Informations du paiement
    type_paiement = models.CharField(
        _('Type de paiement'),
        max_length=20,
        choices=TYPE_CHOICES,
        help_text="Type de paiement effectué"
    )
    
    montant = models.DecimalField(
        _('Montant'),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Montant du paiement en FCFA"
    )
    
    frais = models.DecimalField(
        _('Frais'),
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Frais de transaction en FCFA"
    )
    
    montant_net = models.DecimalField(
        _('Montant net'),
        max_digits=12,
        decimal_places=2,
        help_text="Montant net reçu (montant - frais)"
    )
    
    statut = models.CharField(
        _('Statut'),
        max_length=20,
        choices=STATUT_CHOICES,
        default='EN_ATTENTE',
        help_text="Statut du paiement"
    )
    
    methode_paiement = models.CharField(
        _('Méthode de paiement'),
        max_length=20,
        choices=METHODE_CHOICES,
        help_text="Méthode de paiement utilisée"
    )
    
    # Références externes
    reference_externe = models.CharField(
        _('Référence externe'),
        max_length=100,
        blank=True,
        help_text="Référence du prestataire de paiement"
    )
    
    reference_interne = models.CharField(
        _('Référence interne'),
        max_length=50,
        blank=True,
        help_text="Référence interne SpotVibe"
    )
    
    # Relations optionnelles
    subscription = models.ForeignKey(
        'subscriptions.Subscription',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments',
        verbose_name=_('Abonnement'),
        help_text="Abonnement concerné (si applicable)"
    )
    
    event_ticket = models.ForeignKey(
        EventTicket,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments',
        verbose_name=_('Billet'),
        help_text="Billet concerné (si applicable)"
    )
    
    # Métadonnées
    description = models.TextField(
        _('Description'),
        blank=True,
        help_text="Description du paiement"
    )
    
    date_creation = models.DateTimeField(
        _('Date de création'),
        auto_now_add=True,
        help_text="Date de création du paiement"
    )
    
    date_traitement = models.DateTimeField(
        _('Date de traitement'),
        null=True,
        blank=True,
        help_text="Date de traitement du paiement"
    )
    
    date_expiration = models.DateTimeField(
        _('Date d\'expiration'),
        null=True,
        blank=True,
        help_text="Date d'expiration du paiement"
    )
    
    # Informations de contact
    telephone_paiement = models.CharField(
        _('Téléphone de paiement'),
        max_length=15,
        blank=True,
        help_text="Numéro de téléphone utilisé pour le paiement"
    )
    
    # Données de réponse du prestataire
    donnees_reponse = models.JSONField(
        _('Données de réponse'),
        default=dict,
        blank=True,
        help_text="Données de réponse du prestataire de paiement"
    )
    
    class Meta:
        verbose_name = _('Paiement')
        verbose_name_plural = _('Paiements')
        ordering = ['-date_creation']
        indexes = [
            models.Index(fields=['utilisateur', 'statut']),
            models.Index(fields=['type_paiement', 'statut']),
            models.Index(fields=['reference_externe']),
            models.Index(fields=['date_creation']),
        ]
    
    def __str__(self):
        """Représentation string du paiement."""
        return f"Paiement {self.uuid} - {self.montant} FCFA ({self.statut})"
    
    def save(self, *args, **kwargs):
        """Sauvegarde avec calcul automatique du montant net."""
        self.montant_net = self.montant - self.frais
        
        # Générer une référence interne si elle n'existe pas
        if not self.reference_interne:
            self.reference_interne = f"SV{timezone.now().strftime('%Y%m%d')}{self.id or ''}"
        
        super().save(*args, **kwargs)
    
    def is_successful(self):
        """Vérifie si le paiement est réussi."""
        return self.statut == 'REUSSI'
    
    def can_be_refunded(self):
        """Vérifie si le paiement peut être remboursé."""
        return (
            self.statut == 'REUSSI' and
            self.type_paiement in ['BILLET', 'ABONNEMENT']
        )
    
    def get_commission_amount(self):
        """Calcule le montant de commission pour ce paiement."""
        if self.type_paiement == 'BILLET' and self.event_ticket:
            event = self.event_ticket.evenement
            commission_rate = event.commission_billetterie
            return self.montant * (commission_rate / 100)
        return 0


class MomoTransaction(models.Model):
    """
    Modèle spécifique pour les transactions Mobile Money.
    
    Stocke les détails spécifiques aux transactions Mobile Money
    avec les différents opérateurs du Bénin.
    """
    
    OPERATEUR_CHOICES = [
        ('MTN', _('MTN Bénin')),
        ('MOOV', _('Moov Africa Bénin')),
    ]
    
    TYPE_TRANSACTION_CHOICES = [
        ('PAYMENT', _('Paiement')),
        ('REFUND', _('Remboursement')),
        ('TRANSFER', _('Transfert')),
    ]
    
    payment = models.OneToOneField(
        Payment,
        on_delete=models.CASCADE,
        related_name='momo_transaction',
        verbose_name=_('Paiement'),
        help_text="Paiement associé"
    )
    
    operateur = models.CharField(
        _('Opérateur'),
        max_length=10,
        choices=OPERATEUR_CHOICES,
        help_text="Opérateur Mobile Money"
    )
    
    numero_telephone = models.CharField(
        _('Numéro de téléphone'),
        max_length=15,
        help_text="Numéro de téléphone Mobile Money"
    )
    
    type_transaction = models.CharField(
        _('Type de transaction'),
        max_length=20,
        choices=TYPE_TRANSACTION_CHOICES,
        default='PAYMENT',
        help_text="Type de transaction Mobile Money"
    )
    
    # Identifiants de transaction
    transaction_id = models.CharField(
        _('ID de transaction'),
        max_length=100,
        unique=True,
        help_text="Identifiant unique de la transaction chez l'opérateur"
    )
    
    reference_operateur = models.CharField(
        _('Référence opérateur'),
        max_length=100,
        blank=True,
        help_text="Référence fournie par l'opérateur"
    )
    
    # Détails de la transaction
    code_reponse = models.CharField(
        _('Code de réponse'),
        max_length=10,
        blank=True,
        help_text="Code de réponse de l'opérateur"
    )
    
    message_reponse = models.TextField(
        _('Message de réponse'),
        blank=True,
        help_text="Message de réponse de l'opérateur"
    )
    
    # Métadonnées
    date_initiation = models.DateTimeField(
        _('Date d\'initiation'),
        auto_now_add=True,
        help_text="Date d'initiation de la transaction"
    )
    
    date_confirmation = models.DateTimeField(
        _('Date de confirmation'),
        null=True,
        blank=True,
        help_text="Date de confirmation par l'opérateur"
    )
    
    webhook_recu = models.BooleanField(
        _('Webhook reçu'),
        default=False,
        help_text="Webhook de confirmation reçu"
    )
    
    donnees_webhook = models.JSONField(
        _('Données webhook'),
        default=dict,
        blank=True,
        help_text="Données reçues via webhook"
    )
    
    class Meta:
        verbose_name = _('Transaction Mobile Money')
        verbose_name_plural = _('Transactions Mobile Money')
        ordering = ['-date_initiation']
    
    def __str__(self):
        """Représentation string de la transaction."""
        return f"MoMo {self.operateur} - {self.transaction_id}"
    
    def is_confirmed(self):
        """Vérifie si la transaction est confirmée."""
        return self.date_confirmation is not None and self.webhook_recu


class Commission(models.Model):
    """
    Modèle pour les commissions perçues par la plateforme.
    
    Suit toutes les commissions générées par :
    - Ventes de billets
    - Abonnements
    - Services premium
    """
    
    TYPE_CHOICES = [
        ('BILLETTERIE', _('Commission billetterie')),
        ('ABONNEMENT', _('Commission abonnement')),
        ('SERVICE', _('Commission service')),
    ]
    
    STATUT_CHOICES = [
        ('EN_ATTENTE', _('En attente')),
        ('CALCULEE', _('Calculée')),
        ('PAYEE', _('Payée')),
        ('ANNULEE', _('Annulée')),
    ]
    
    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        related_name='commissions',
        verbose_name=_('Paiement'),
        help_text="Paiement générateur de commission"
    )
    
    type_commission = models.CharField(
        _('Type de commission'),
        max_length=20,
        choices=TYPE_CHOICES,
        help_text="Type de commission"
    )
    
    montant_base = models.DecimalField(
        _('Montant de base'),
        max_digits=12,
        decimal_places=2,
        help_text="Montant sur lequel la commission est calculée"
    )
    
    taux_commission = models.DecimalField(
        _('Taux de commission'),
        max_digits=5,
        decimal_places=2,
        help_text="Taux de commission en pourcentage"
    )
    
    montant_commission = models.DecimalField(
        _('Montant de commission'),
        max_digits=10,
        decimal_places=2,
        help_text="Montant de commission calculé"
    )
    
    statut = models.CharField(
        _('Statut'),
        max_length=20,
        choices=STATUT_CHOICES,
        default='EN_ATTENTE',
        help_text="Statut de la commission"
    )
    
    # Relations optionnelles
    event = models.ForeignKey(
        'events.Event',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='commissions',
        verbose_name=_('Événement'),
        help_text="Événement concerné (si applicable)"
    )
    
    organisateur = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='commissions_dues',
        verbose_name=_('Organisateur'),
        help_text="Organisateur qui doit la commission"
    )
    
    # Métadonnées
    date_calcul = models.DateTimeField(
        _('Date de calcul'),
        auto_now_add=True,
        help_text="Date de calcul de la commission"
    )
    
    date_paiement = models.DateTimeField(
        _('Date de paiement'),
        null=True,
        blank=True,
        help_text="Date de paiement de la commission"
    )
    
    notes = models.TextField(
        _('Notes'),
        blank=True,
        help_text="Notes sur la commission"
    )
    
    class Meta:
        verbose_name = _('Commission')
        verbose_name_plural = _('Commissions')
        ordering = ['-date_calcul']
        indexes = [
            models.Index(fields=['organisateur', 'statut']),
            models.Index(fields=['type_commission', 'statut']),
            models.Index(fields=['date_calcul']),
        ]
    
    def __str__(self):
        """Représentation string de la commission."""
        return f"Commission {self.type_commission} - {self.montant_commission} FCFA"
    
    def save(self, *args, **kwargs):
        """Sauvegarde avec calcul automatique du montant."""
        self.montant_commission = self.montant_base * (self.taux_commission / 100)
        super().save(*args, **kwargs)


class Refund(models.Model):
    """
    Modèle pour les remboursements.
    
    Gère les demandes et traitements de remboursement
    pour les billets et abonnements.
    """
    
    STATUT_CHOICES = [
        ('DEMANDE', _('Demandé')),
        ('EN_COURS', _('En cours')),
        ('APPROUVE', _('Approuvé')),
        ('REJETE', _('Rejeté')),
        ('REMBOURSE', _('Remboursé')),
    ]
    
    RAISON_CHOICES = [
        ('ANNULATION_EVENT', _('Annulation d\'événement')),
        ('DEMANDE_CLIENT', _('Demande client')),
        ('ERREUR_PAIEMENT', _('Erreur de paiement')),
        ('FRAUDE', _('Fraude détectée')),
        ('AUTRE', _('Autre raison')),
    ]
    
    payment_original = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        related_name='refunds',
        verbose_name=_('Paiement original'),
        help_text="Paiement à rembourser"
    )
    
    demandeur = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='refunds_requested',
        verbose_name=_('Demandeur'),
        help_text="Utilisateur qui demande le remboursement"
    )
    
    montant_remboursement = models.DecimalField(
        _('Montant de remboursement'),
        max_digits=12,
        decimal_places=2,
        help_text="Montant à rembourser"
    )
    
    raison = models.CharField(
        _('Raison'),
        max_length=30,
        choices=RAISON_CHOICES,
        help_text="Raison du remboursement"
    )
    
    description = models.TextField(
        _('Description'),
        help_text="Description détaillée de la demande"
    )
    
    statut = models.CharField(
        _('Statut'),
        max_length=20,
        choices=STATUT_CHOICES,
        default='DEMANDE',
        help_text="Statut du remboursement"
    )
    
    # Traitement
    date_demande = models.DateTimeField(
        _('Date de demande'),
        auto_now_add=True,
        help_text="Date de la demande de remboursement"
    )
    
    date_traitement = models.DateTimeField(
        _('Date de traitement'),
        null=True,
        blank=True,
        help_text="Date de traitement de la demande"
    )
    
    date_remboursement = models.DateTimeField(
        _('Date de remboursement'),
        null=True,
        blank=True,
        help_text="Date effective du remboursement"
    )
    
    traiteur = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='refunds_processed',
        verbose_name=_('Traiteur'),
        help_text="Administrateur qui a traité la demande"
    )
    
    commentaire_admin = models.TextField(
        _('Commentaire administrateur'),
        blank=True,
        help_text="Commentaire de l'administrateur"
    )
    
    # Paiement de remboursement
    payment_remboursement = models.OneToOneField(
        Payment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='refund_source',
        verbose_name=_('Paiement de remboursement'),
        help_text="Paiement effectué pour le remboursement"
    )
    
    class Meta:
        verbose_name = _('Remboursement')
        verbose_name_plural = _('Remboursements')
        ordering = ['-date_demande']
    
    def __str__(self):
        """Représentation string du remboursement."""
        return f"Remboursement {self.montant_remboursement} FCFA - {self.statut}"
    
    def can_be_processed(self):
        """Vérifie si le remboursement peut être traité."""
        return self.statut == 'DEMANDE' and self.payment_original.can_be_refunded()
    
    def approve(self, admin_user, comment=""):
        """Approuve la demande de remboursement."""
        self.statut = 'APPROUVE'
        self.traiteur = admin_user
        self.commentaire_admin = comment
        self.date_traitement = timezone.now()
        self.save()
    
    def reject(self, admin_user, comment=""):
        """Rejette la demande de remboursement."""
        self.statut = 'REJETE'
        self.traiteur = admin_user
        self.commentaire_admin = comment
        self.date_traitement = timezone.now()
        self.save()

