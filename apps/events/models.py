"""
Modèles pour la gestion des événements dans SpotVibe.

Ce module définit tous les modèles liés aux événements :
- EventCategory : Catégories d'événements
- Event : Événements principaux
- EventParticipation : Participation aux événements
- EventShare : Partages d'événements
- EventTicket : Billetterie
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from PIL import Image
import qrcode
from io import BytesIO
from django.core.files import File
import uuid

User = get_user_model()


class EventCategory(models.Model):
    """
    Modèle pour les catégories d'événements.
    
    Permet de classer les événements par type (mariage, festival, etc.)
    avec des icônes et couleurs personnalisées.
    """
    
    nom = models.CharField(
        _('Nom'),
        max_length=100,
        unique=True,
        help_text="Nom de la catégorie (ex: Mariage, Festival, Conférence)"
    )
    
    description = models.TextField(
        _('Description'),
        blank=True,
        help_text="Description de la catégorie"
    )
    
    icone = models.CharField(
        _('Icône'),
        max_length=50,
        blank=True,
        help_text="Nom de l'icône (ex: fas fa-music)"
    )
    
    couleur = models.CharField(
        _('Couleur'),
        max_length=7,
        default='#007bff',
        help_text="Couleur hexadécimale (ex: #007bff)"
    )
    
    ordre = models.PositiveIntegerField(
        _('Ordre d\'affichage'),
        default=0,
        help_text="Ordre d'affichage dans les listes"
    )
    
    actif = models.BooleanField(
        _('Actif'),
        default=True,
        help_text="Catégorie active et visible"
    )
    
    class Meta:
        verbose_name = _('Catégorie d\'événement')
        verbose_name_plural = _('Catégories d\'événement')
        ordering = ['ordre', 'nom']
    
    def __str__(self):
        """Représentation string de la catégorie."""
        return self.nom
    
    def get_events_count(self):
        """Retourne le nombre d'événements dans cette catégorie."""
        return self.events.filter(statut='VALIDE').count()


class Event(models.Model):
    """
    Modèle principal pour les événements.
    
    Contient toutes les informations d'un événement :
    - Informations de base (titre, description, dates)
    - Localisation et cartographie
    - Gestion des participants et billets
    - Statut de validation
    """
    
    STATUT_CHOICES = [
        ('BROUILLON', _('Brouillon')),
        ('EN_ATTENTE', _('En attente de validation')),
        ('VALIDE', _('Validé')),
        ('REJETE', _('Rejeté')),
        ('ANNULE', _('Annulé')),
        ('TERMINE', _('Terminé')),
    ]
    
    TYPE_ACCES_CHOICES = [
        ('GRATUIT', _('Gratuit')),
        ('PAYANT', _('Payant')),
        ('INVITATION', _('Sur invitation')),
    ]
    
    # Informations de base
    titre = models.CharField(
        _('Titre'),
        max_length=200,
        help_text="Titre de l'événement"
    )
    
    description = models.TextField(
        _('Description'),
        help_text="Description détaillée de l'événement"
    )
    
    description_courte = models.CharField(
        _('Description courte'),
        max_length=300,
        blank=True,
        help_text="Résumé court pour les listes"
    )
    
    # Dates et horaires
    date_debut = models.DateTimeField(
        _('Date de début'),
        help_text="Date et heure de début de l'événement"
    )
    
    date_fin = models.DateTimeField(
        _('Date de fin'),
        help_text="Date et heure de fin de l'événement"
    )
    
    # Localisation
    lieu = models.CharField(
        _('Lieu'),
        max_length=300,
        help_text="Nom du lieu de l'événement"
    )
    
    adresse = models.TextField(
        _('Adresse'),
        help_text="Adresse complète du lieu"
    )
    
    latitude = models.DecimalField(
        _('Latitude'),
        max_digits=10,
        decimal_places=8,
        null=True,
        blank=True,
        help_text="Coordonnée latitude pour la carte"
    )
    
    longitude = models.DecimalField(
        _('Longitude'),
        max_digits=11,
        decimal_places=8,
        null=True,
        blank=True,
        help_text="Coordonnée longitude pour la carte"
    )
    
    lien_google_maps = models.URLField(
        _('Lien Google Maps'),
        blank=True,
        help_text="Lien vers Google Maps pour le lieu"
    )
    
    # Relations
    createur = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='events_created',
        verbose_name=_('Créateur'),
        help_text="Utilisateur qui a créé l'événement"
    )
    
    categorie = models.ForeignKey(
        EventCategory,
        on_delete=models.SET_NULL,
        null=True,
        related_name='events',
        verbose_name=_('Catégorie'),
        help_text="Catégorie de l'événement"
    )
    
    # Accès et tarification
    type_acces = models.CharField(
        _('Type d\'accès'),
        max_length=20,
        choices=TYPE_ACCES_CHOICES,
        default='GRATUIT',
        help_text="Type d'accès à l'événement"
    )
    
    prix = models.DecimalField(
        _('Prix'),
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Prix d'entrée en FCFA"
    )
    
    capacite_max = models.PositiveIntegerField(
        _('Capacité maximale'),
        null=True,
        blank=True,
        help_text="Nombre maximum de participants (optionnel)"
    )
    
    # Images
    image_couverture = models.ImageField(
        _('Image de couverture'),
        upload_to='events/covers/',
        help_text="Image principale de l'événement"
    )
    
    # Statut et validation
    statut = models.CharField(
        _('Statut'),
        max_length=20,
        choices=STATUT_CHOICES,
        default='BROUILLON',
        help_text="Statut de l'événement"
    )
    
    date_validation = models.DateTimeField(
        _('Date de validation'),
        null=True,
        blank=True,
        help_text="Date de validation par un administrateur"
    )
    
    validateur = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='events_validated',
        verbose_name=_('Validateur'),
        help_text="Administrateur qui a validé l'événement"
    )
    
    commentaire_validation = models.TextField(
        _('Commentaire de validation'),
        blank=True,
        help_text="Commentaire de l'administrateur"
    )
    
    # Statistiques
    nombre_vues = models.PositiveIntegerField(
        _('Nombre de vues'),
        default=0,
        help_text="Nombre de fois que l'événement a été consulté"
    )
    
    nombre_partages = models.PositiveIntegerField(
        _('Nombre de partages'),
        default=0,
        help_text="Nombre de fois que l'événement a été partagé"
    )
    
    # Métadonnées
    date_creation = models.DateTimeField(
        _('Date de création'),
        auto_now_add=True,
        help_text="Date de création de l'événement"
    )
    
    date_modification = models.DateTimeField(
        _('Date de modification'),
        auto_now=True,
        help_text="Date de dernière modification"
    )
    
    # Billetterie
    billetterie_activee = models.BooleanField(
        _('Billetterie activée'),
        default=False,
        help_text="Utiliser le système de billetterie intégré"
    )
    
    commission_billetterie = models.DecimalField(
        _('Commission billetterie'),
        max_digits=5,
        decimal_places=2,
        default=10.00,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Commission en pourcentage sur les ventes"
    )
    
    class Meta:
        verbose_name = _('Événement')
        verbose_name_plural = _('Événements')
        ordering = ['-date_creation']
        indexes = [
            models.Index(fields=['statut', 'date_debut']),
            models.Index(fields=['createur', 'statut']),
            models.Index(fields=['categorie', 'statut']),
        ]
    
    def __str__(self):
        """Représentation string de l'événement."""
        return f"{self.titre} - {self.date_debut.strftime('%d/%m/%Y')}"
    
    def save(self, *args, **kwargs):
        """
        Sauvegarde personnalisée pour redimensionner l'image de couverture
        et mettre à jour le statut automatiquement.
        """
        # Marquer comme terminé si la date est passée
        if self.date_fin < timezone.now() and self.statut == 'VALIDE':
            self.statut = 'TERMINE'
        
        super().save(*args, **kwargs)
        
        # Redimensionner l'image de couverture
        if self.image_couverture:
            img = Image.open(self.image_couverture.path)
            if img.height > 600 or img.width > 800:
                output_size = (800, 600)
                img.thumbnail(output_size)
                img.save(self.image_couverture.path)
    
    def get_participants_count(self):
        """Retourne le nombre de participants à l'événement."""
        return self.participations.filter(statut='PARTICIPE').count()
    
    def get_interested_count(self):
        """Retourne le nombre d'utilisateurs intéressés."""
        return self.participations.filter(statut='INTERESSE').count()
    
    def is_full(self):
        """Vérifie si l'événement est complet."""
        if not self.capacite_max:
            return False
        return self.get_participants_count() >= self.capacite_max
    
    def is_past(self):
        """Vérifie si l'événement est passé."""
        return self.date_fin < timezone.now()
    
    def can_participate(self, user):
        """Vérifie si un utilisateur peut participer à l'événement."""
        if self.is_past() or self.statut != 'VALIDE':
            return False
        
        if self.is_full():
            return False
        
        # Vérifier si l'utilisateur n'est pas déjà inscrit
        return not self.participations.filter(
            utilisateur=user,
            statut__in=['PARTICIPE', 'INTERESSE']
        ).exists()
    
    def get_revenue(self):
        """Calcule le revenu total de l'événement."""
        if not self.billetterie_activee:
            return 0
        
        total = self.tickets.filter(statut='PAYE').aggregate(
            total=models.Sum('prix')
        )['total'] or 0
        
        return total
    
    def get_commission_amount(self):
        """Calcule le montant de commission sur les ventes."""
        revenue = self.get_revenue()
        return revenue * (self.commission_billetterie / 100)


class EventParticipation(models.Model):
    """
    Modèle pour la participation aux événements.
    
    Gère les différents types de participation :
    - Intéressé (like)
    - Participe (inscription confirmée)
    - A participé (après l'événement)
    """
    
    STATUT_CHOICES = [
        ('INTERESSE', _('Intéressé')),
        ('PARTICIPE', _('Participe')),
        ('A_PARTICIPE', _('A participé')),
        ('ANNULE', _('Annulé')),
    ]
    
    utilisateur = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='participations',
        verbose_name=_('Utilisateur'),
        help_text="Utilisateur participant"
    )
    
    evenement = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='participations',
        verbose_name=_('Événement'),
        help_text="Événement concerné"
    )
    
    statut = models.CharField(
        _('Statut'),
        max_length=20,
        choices=STATUT_CHOICES,
        default='INTERESSE',
        help_text="Type de participation"
    )
    
    date_participation = models.DateTimeField(
        _('Date de participation'),
        auto_now_add=True,
        help_text="Date d'inscription à l'événement"
    )
    
    date_modification = models.DateTimeField(
        _('Date de modification'),
        auto_now=True,
        help_text="Date de dernière modification du statut"
    )
    
    commentaire = models.TextField(
        _('Commentaire'),
        blank=True,
        help_text="Commentaire du participant"
    )
    
    class Meta:
        verbose_name = _('Participation à un événement')
        verbose_name_plural = _('Participations aux événements')
        unique_together = ['utilisateur', 'evenement']
        ordering = ['-date_participation']
    
    def __str__(self):
        """Représentation string de la participation."""
        return f"{self.utilisateur.username} - {self.evenement.titre} ({self.statut})"


class EventShare(models.Model):
    """
    Modèle pour le partage d'événements sur les réseaux sociaux.
    
    Suit les partages d'événements et génère des liens personnalisés
    pour augmenter la visibilité de la plateforme.
    """
    
    PLATEFORME_CHOICES = [
        ('FACEBOOK', _('Facebook')),
        ('TWITTER', _('Twitter')),
        ('INSTAGRAM', _('Instagram')),
        ('WHATSAPP', _('WhatsApp')),
        ('LINKEDIN', _('LinkedIn')),
        ('EMAIL', _('Email')),
        ('LIEN', _('Lien direct')),
    ]
    
    utilisateur = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='partages',
        verbose_name=_('Utilisateur'),
        help_text="Utilisateur qui partage"
    )
    
    evenement = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='partages',
        verbose_name=_('Événement'),
        help_text="Événement partagé"
    )
    
    plateforme = models.CharField(
        _('Plateforme'),
        max_length=20,
        choices=PLATEFORME_CHOICES,
        help_text="Plateforme de partage"
    )
    
    date_partage = models.DateTimeField(
        _('Date de partage'),
        auto_now_add=True,
        help_text="Date du partage"
    )
    
    lien_genere = models.URLField(
        _('Lien généré'),
        blank=True,
        help_text="Lien personnalisé généré pour le partage"
    )
    
    nombre_clics = models.PositiveIntegerField(
        _('Nombre de clics'),
        default=0,
        help_text="Nombre de clics sur le lien partagé"
    )
    
    class Meta:
        verbose_name = _('Partage d\'événement')
        verbose_name_plural = _('Partages d\'événement')
        ordering = ['-date_partage']
    
    def __str__(self):
        """Représentation string du partage."""
        return f"{self.utilisateur.username} partage {self.evenement.titre} sur {self.plateforme}"


class EventTicket(models.Model):
    """
    Modèle pour la billetterie des événements.
    
    Gère les billets vendus via la plateforme avec :
    - Génération de codes QR
    - Suivi des paiements
    - Validation à l'entrée
    """
    
    STATUT_CHOICES = [
        ('EN_ATTENTE', _('En attente de paiement')),
        ('PAYE', _('Payé')),
        ('ANNULE', _('Annulé')),
        ('REMBOURSE', _('Remboursé')),
        ('UTILISE', _('Utilisé')),
    ]
    
    # Identifiant unique du billet
    uuid = models.UUIDField(
        _('Identifiant unique'),
        default=uuid.uuid4,
        editable=False,
        unique=True,
        help_text="Identifiant unique du billet"
    )
    
    evenement = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='tickets',
        verbose_name=_('Événement'),
        help_text="Événement concerné"
    )
    
    utilisateur = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='tickets',
        verbose_name=_('Utilisateur'),
        help_text="Acheteur du billet"
    )
    
    prix = models.DecimalField(
        _('Prix'),
        max_digits=10,
        decimal_places=2,
        help_text="Prix payé pour le billet"
    )
    
    quantite = models.PositiveIntegerField(
        _('Quantité'),
        default=1,
        help_text="Nombre de billets"
    )
    
    statut = models.CharField(
        _('Statut'),
        max_length=20,
        choices=STATUT_CHOICES,
        default='EN_ATTENTE',
        help_text="Statut du billet"
    )
    
    code_qr = models.ImageField(
        _('Code QR'),
        upload_to='tickets/qr/',
        blank=True,
        help_text="Code QR pour la validation"
    )
    
    date_achat = models.DateTimeField(
        _('Date d\'achat'),
        auto_now_add=True,
        help_text="Date d'achat du billet"
    )
    
    date_utilisation = models.DateTimeField(
        _('Date d\'utilisation'),
        null=True,
        blank=True,
        help_text="Date d'utilisation du billet"
    )
    
    reference_paiement = models.CharField(
        _('Référence de paiement'),
        max_length=100,
        blank=True,
        help_text="Référence du paiement Mobile Money"
    )
    
    class Meta:
        verbose_name = _('Billet d\'événement')
        verbose_name_plural = _('Billets d\'événement')
        ordering = ['-date_achat']
    
    def __str__(self):
        """Représentation string du billet."""
        return f"Billet {self.uuid} - {self.evenement.titre}"
    
    def save(self, *args, **kwargs):
        """Sauvegarde avec génération automatique du code QR."""
        super().save(*args, **kwargs)
        
        # Générer le code QR si le billet est payé et qu'il n'existe pas
        if self.statut == 'PAYE' and not self.code_qr:
            self.generate_qr_code()
    
    def generate_qr_code(self):
        """Génère un code QR pour le billet."""
        # Données à encoder dans le QR code
        qr_data = f"SPOTVIBE-{self.uuid}-{self.evenement.id}"
        
        # Créer le QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        # Créer l'image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Sauvegarder dans un buffer
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        # Sauvegarder le fichier
        filename = f"qr_{self.uuid}.png"
        self.code_qr.save(filename, File(buffer), save=True)
        buffer.close()
    
    def get_total_price(self):
        """Calcule le prix total (prix × quantité)."""
        return self.prix * self.quantite
    
    def can_be_used(self):
        """Vérifie si le billet peut être utilisé."""
        return (
            self.statut == 'PAYE' and
            not self.evenement.is_past() and
            self.evenement.statut == 'VALIDE'
        )

