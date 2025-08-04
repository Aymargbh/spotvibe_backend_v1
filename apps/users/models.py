"""
Modèles pour la gestion des utilisateurs dans SpotVibe.

Ce module définit le modèle User personnalisé qui étend AbstractUser de Django
avec des champs supplémentaires spécifiques à l'application SpotVibe.
Il inclut également les modèles pour la vérification d'identité et le suivi entre utilisateurs.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _
from PIL import Image
import os


class User(AbstractUser):
    """
    Modèle utilisateur personnalisé pour SpotVibe.
    
    Étend AbstractUser avec des champs spécifiques à l'application :
    - Informations personnelles (téléphone, date de naissance, photo)
    - Statut de vérification
    - Préférences de notification
    """
    
    # Validation du numéro de téléphone (format béninois)
    phone_regex = RegexValidator(
        regex=r'^\+229[0-9]{10}$',
        message="Le numéro de téléphone doit être au format: '+229XXXXXXXX'."
    )
    
    # Champs supplémentaires
    telephone = models.CharField(
        _('Téléphone'),
        validators=[phone_regex],
        max_length=15,
        unique=True,
        help_text="Numéro de téléphone au format béninois (+229XXXXXXXX)"
    )
    
    date_naissance = models.DateField(
        _('Date de naissance'),
        null=True,
        blank=True,
        help_text="Date de naissance de l'utilisateur"
    )
    
    photo_profil = models.ImageField(
        _('Photo de profil'),
        upload_to='profiles/',
        null=True,
        blank=True,
        help_text="Photo de profil de l'utilisateur (max 5MB)"
    )
    
    bio = models.TextField(
        _('Biographie'),
        max_length=500,
        blank=True,
        help_text="Description courte de l'utilisateur"
    )
    
    # Statut de vérification
    est_verifie = models.BooleanField(
        _('Compte vérifié'),
        default=False,
        help_text="Indique si l'utilisateur a vérifié son identité"
    )
    
    date_verification = models.DateTimeField(
        _('Date de vérification'),
        null=True,
        blank=True,
        help_text="Date à laquelle le compte a été vérifié"
    )
    
    # Préférences de notification
    notifications_email = models.BooleanField(
        _('Notifications par email'),
        default=True,
        help_text="Recevoir les notifications par email"
    )
    
    notifications_push = models.BooleanField(
        _('Notifications push'),
        default=True,
        help_text="Recevoir les notifications push"
    )
    
    # Métadonnées
    date_creation = models.DateTimeField(
        _('Date de création'),
        auto_now_add=True,
        help_text="Date de création du compte"
    )
    
    date_modification = models.DateTimeField(
        _('Date de modification'),
        auto_now=True,
        help_text="Date de dernière modification du profil"
    )
    
    derniere_connexion_ip = models.GenericIPAddressField(
        _('Dernière IP de connexion'),
        null=True,
        blank=True,
        help_text="Adresse IP de la dernière connexion"
    )
    
    class Meta:
        verbose_name = _('Utilisateur')
        verbose_name_plural = _('Utilisateurs')
        ordering = ['-date_creation']
    
    def __str__(self):
        """Représentation string de l'utilisateur."""
        return f"{self.username} ({self.get_full_name() or self.email})"
    
    def save(self, *args, **kwargs):
        """
        Sauvegarde personnalisée pour redimensionner la photo de profil.
        Redimensionne automatiquement les images trop grandes.
        """
        super().save(*args, **kwargs)
        
        if self.photo_profil:
            img = Image.open(self.photo_profil.path)
            
            # Redimensionner si l'image est trop grande
            if img.height > 300 or img.width > 300:
                output_size = (300, 300)
                img.thumbnail(output_size)
                img.save(self.photo_profil.path)
    
    def get_full_name(self):
        """Retourne le nom complet de l'utilisateur."""
        return f"{self.first_name} {self.last_name}".strip()
    
    def get_events_count(self):
        """Retourne le nombre d'événements créés par l'utilisateur."""
        return self.events_created.count()
    
    def get_followers_count(self):
        """Retourne le nombre de followers de l'utilisateur."""
        return self.followers.count()
    
    def get_following_count(self):
        """Retourne le nombre d'utilisateurs suivis."""
        return self.following.count()
    
    def can_create_event(self):
        """
        Vérifie si l'utilisateur peut créer un événement.
        Les utilisateurs non vérifiés sont limités à 1 événement.
        """
        if self.est_verifie:
            return True
        
        from django.conf import settings
        max_events = settings.SPOTVIBE_SETTINGS.get('MAX_EVENTS_UNVERIFIED', 1)
        return self.get_events_count() < max_events


class UserVerification(models.Model):
    """
    Modèle pour la vérification d'identité des utilisateurs.
    
    Stocke les documents d'identité soumis par les utilisateurs
    et le statut de validation par les administrateurs.
    """
    
    STATUT_CHOICES = [
        ('EN_ATTENTE', _('En attente')),
        ('APPROUVE', _('Approuvé')),
        ('REJETE', _('Rejeté')),
        ('EXPIRE', _('Expiré')),
    ]
    
    utilisateur = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='verification',
        verbose_name=_('Utilisateur'),
        help_text="Utilisateur concerné par la vérification"
    )
    
    document_identite = models.FileField(
        _('Document d\'identité'),
        upload_to='verifications/',
        help_text="Carte d'identité, passeport ou autre document officiel"
    )
    
    document_selfie = models.ImageField(
        _('Selfie avec document'),
        upload_to='verifications/',
        null=True,
        blank=True,
        help_text="Photo de l'utilisateur tenant son document d'identité"
    )
    
    statut = models.CharField(
        _('Statut'),
        max_length=20,
        choices=STATUT_CHOICES,
        default='EN_ATTENTE',
        help_text="Statut de la vérification"
    )
    
    date_soumission = models.DateTimeField(
        _('Date de soumission'),
        auto_now_add=True,
        help_text="Date de soumission des documents"
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
        related_name='verifications_validees',
        verbose_name=_('Validateur'),
        help_text="Administrateur qui a validé la vérification"
    )
    
    commentaire_admin = models.TextField(
        _('Commentaire administrateur'),
        blank=True,
        help_text="Commentaire de l'administrateur sur la vérification"
    )
    
    class Meta:
        verbose_name = _('Vérification utilisateur')
        verbose_name_plural = _('Vérifications utilisateur')
        ordering = ['-date_soumission']
    
    def __str__(self):
        """Représentation string de la vérification."""
        return f"Vérification de {self.utilisateur.username} - {self.statut}"


class Follow(models.Model):
    """
    Modèle pour le système de suivi entre utilisateurs.
    
    Permet aux utilisateurs de suivre d'autres utilisateurs
    et de recevoir des notifications sur leurs activités.
    """
    
    follower = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name=_('Suiveur'),
        help_text="Utilisateur qui suit"
    )
    
    following = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='followers',
        verbose_name=_('Suivi'),
        help_text="Utilisateur suivi"
    )
    
    date_suivi = models.DateTimeField(
        _('Date de suivi'),
        auto_now_add=True,
        help_text="Date à laquelle le suivi a commencé"
    )
    
    notifications_activees = models.BooleanField(
        _('Notifications activées'),
        default=True,
        help_text="Recevoir des notifications pour les activités de cet utilisateur"
    )
    
    class Meta:
        verbose_name = _('Suivi')
        verbose_name_plural = _('Suivis')
        unique_together = ['follower', 'following']
        ordering = ['-date_suivi']
    
    def __str__(self):
        """Représentation string du suivi."""
        return f"{self.follower.username} suit {self.following.username}"
    
    def clean(self):
        """Validation personnalisée pour empêcher l'auto-suivi."""
        from django.core.exceptions import ValidationError
        
        if self.follower == self.following:
            raise ValidationError(_("Un utilisateur ne peut pas se suivre lui-même."))
    
    def save(self, *args, **kwargs):
        """Sauvegarde avec validation."""
        self.clean()
        super().save(*args, **kwargs)

