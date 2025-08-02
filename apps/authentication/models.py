"""
Modèles pour l'authentification dans SpotVibe.

Ce module définit les modèles pour :
- SocialAccount : Comptes de réseaux sociaux liés
- LoginAttempt : Tentatives de connexion
- PasswordReset : Réinitialisations de mot de passe
- EmailVerification : Vérifications d'email
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import timedelta
import secrets
import string

User = get_user_model()


class SocialAccount(models.Model):
    """
    Modèle pour les comptes de réseaux sociaux liés.
    
    Stocke les informations des comptes Google et Facebook
    liés aux comptes utilisateurs.
    """
    
    PROVIDER_CHOICES = [
        ('GOOGLE', _('Google')),
        ('FACEBOOK', _('Facebook')),
    ]
    
    utilisateur = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='social_accounts',
        verbose_name=_('Utilisateur'),
        help_text="Utilisateur propriétaire du compte social"
    )
    
    provider = models.CharField(
        _('Fournisseur'),
        max_length=20,
        choices=PROVIDER_CHOICES,
        help_text="Fournisseur du compte social"
    )
    
    social_id = models.CharField(
        _('ID social'),
        max_length=100,
        help_text="Identifiant unique chez le fournisseur"
    )
    
    email = models.EmailField(
        _('Email'),
        help_text="Email associé au compte social"
    )
    
    nom_complet = models.CharField(
        _('Nom complet'),
        max_length=200,
        blank=True,
        help_text="Nom complet récupéré du compte social"
    )
    
    photo_url = models.URLField(
        _('URL de la photo'),
        blank=True,
        help_text="URL de la photo de profil"
    )
    
    # Tokens d'accès
    access_token = models.TextField(
        _('Token d\'accès'),
        blank=True,
        help_text="Token d'accès pour l'API du fournisseur"
    )
    
    refresh_token = models.TextField(
        _('Token de rafraîchissement'),
        blank=True,
        help_text="Token de rafraîchissement"
    )
    
    token_expires_at = models.DateTimeField(
        _('Expiration du token'),
        null=True,
        blank=True,
        help_text="Date d'expiration du token d'accès"
    )
    
    # Métadonnées
    date_creation = models.DateTimeField(
        _('Date de création'),
        auto_now_add=True,
        help_text="Date de liaison du compte"
    )
    
    date_modification = models.DateTimeField(
        _('Date de modification'),
        auto_now=True,
        help_text="Date de dernière modification"
    )
    
    derniere_utilisation = models.DateTimeField(
        _('Dernière utilisation'),
        null=True,
        blank=True,
        help_text="Dernière utilisation pour la connexion"
    )
    
    actif = models.BooleanField(
        _('Actif'),
        default=True,
        help_text="Compte social actif"
    )
    
    class Meta:
        verbose_name = _('Compte social')
        verbose_name_plural = _('Comptes sociaux')
        unique_together = ['provider', 'social_id']
        ordering = ['-date_creation']
    
    def __str__(self):
        """Représentation string du compte social."""
        return f"{self.utilisateur.username} - {self.provider}"
    
    def is_token_valid(self):
        """Vérifie si le token d'accès est encore valide."""
        if not self.token_expires_at:
            return True  # Pas d'expiration définie
        return timezone.now() < self.token_expires_at


class LoginAttempt(models.Model):
    """
    Modèle pour les tentatives de connexion.
    
    Suit les tentatives de connexion pour la sécurité
    et la détection de tentatives d'intrusion.
    """
    
    STATUT_CHOICES = [
        ('REUSSI', _('Réussi')),
        ('ECHEC', _('Échec')),
        ('BLOQUE', _('Bloqué')),
    ]
    
    # Utilisateur (peut être null pour les tentatives avec email inexistant)
    utilisateur = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='login_attempts',
        verbose_name=_('Utilisateur'),
        help_text="Utilisateur concerné (si existant)"
    )
    
    # Informations de tentative
    email_tente = models.EmailField(
        _('Email tenté'),
        help_text="Email utilisé pour la tentative"
    )
    
    statut = models.CharField(
        _('Statut'),
        max_length=10,
        choices=STATUT_CHOICES,
        help_text="Résultat de la tentative"
    )
    
    raison_echec = models.CharField(
        _('Raison de l\'échec'),
        max_length=100,
        blank=True,
        help_text="Raison de l'échec de connexion"
    )
    
    # Informations techniques
    adresse_ip = models.GenericIPAddressField(
        _('Adresse IP'),
        help_text="Adresse IP de la tentative"
    )
    
    user_agent = models.TextField(
        _('User Agent'),
        blank=True,
        help_text="User Agent du navigateur"
    )
    
    # Géolocalisation (optionnelle)
    pays = models.CharField(
        _('Pays'),
        max_length=50,
        blank=True,
        help_text="Pays d'origine de l'IP"
    )
    
    ville = models.CharField(
        _('Ville'),
        max_length=100,
        blank=True,
        help_text="Ville d'origine de l'IP"
    )
    
    # Métadonnées
    date_tentative = models.DateTimeField(
        _('Date de tentative'),
        auto_now_add=True,
        help_text="Date et heure de la tentative"
    )
    
    duree_session = models.DurationField(
        _('Durée de session'),
        null=True,
        blank=True,
        help_text="Durée de la session (pour les connexions réussies)"
    )
    
    class Meta:
        verbose_name = _('Tentative de connexion')
        verbose_name_plural = _('Tentatives de connexion')
        ordering = ['-date_tentative']
        indexes = [
            models.Index(fields=['adresse_ip', 'date_tentative']),
            models.Index(fields=['email_tente', 'date_tentative']),
            models.Index(fields=['utilisateur', 'statut']),
        ]
    
    def __str__(self):
        """Représentation string de la tentative."""
        return f"{self.email_tente} - {self.statut} - {self.date_tentative.strftime('%d/%m/%Y %H:%M')}"
    
    @classmethod
    def get_recent_failures(cls, email, minutes=15):
        """Retourne le nombre d'échecs récents pour un email."""
        since = timezone.now() - timedelta(minutes=minutes)
        return cls.objects.filter(
            email_tente=email,
            statut='ECHEC',
            date_tentative__gte=since
        ).count()
    
    @classmethod
    def is_ip_blocked(cls, ip_address, minutes=60, max_attempts=10):
        """Vérifie si une IP est bloquée."""
        since = timezone.now() - timedelta(minutes=minutes)
        failures = cls.objects.filter(
            adresse_ip=ip_address,
            statut='ECHEC',
            date_tentative__gte=since
        ).count()
        return failures >= max_attempts


class PasswordReset(models.Model):
    """
    Modèle pour les demandes de réinitialisation de mot de passe.
    
    Gère les tokens de réinitialisation avec expiration
    et limitation d'utilisation.
    """
    
    STATUT_CHOICES = [
        ('ACTIF', _('Actif')),
        ('UTILISE', _('Utilisé')),
        ('EXPIRE', _('Expiré')),
        ('ANNULE', _('Annulé')),
    ]
    
    utilisateur = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='password_resets',
        verbose_name=_('Utilisateur'),
        help_text="Utilisateur demandant la réinitialisation"
    )
    
    token = models.CharField(
        _('Token'),
        max_length=64,
        unique=True,
        help_text="Token de réinitialisation"
    )
    
    statut = models.CharField(
        _('Statut'),
        max_length=10,
        choices=STATUT_CHOICES,
        default='ACTIF',
        help_text="Statut du token"
    )
    
    # Dates
    date_creation = models.DateTimeField(
        _('Date de création'),
        auto_now_add=True,
        help_text="Date de création du token"
    )
    
    date_expiration = models.DateTimeField(
        _('Date d\'expiration'),
        help_text="Date d'expiration du token"
    )
    
    date_utilisation = models.DateTimeField(
        _('Date d\'utilisation'),
        null=True,
        blank=True,
        help_text="Date d'utilisation du token"
    )
    
    # Informations de sécurité
    adresse_ip_creation = models.GenericIPAddressField(
        _('IP de création'),
        help_text="IP utilisée pour créer le token"
    )
    
    adresse_ip_utilisation = models.GenericIPAddressField(
        _('IP d\'utilisation'),
        null=True,
        blank=True,
        help_text="IP utilisée pour utiliser le token"
    )
    
    class Meta:
        verbose_name = _('Réinitialisation de mot de passe')
        verbose_name_plural = _('Réinitialisations de mot de passe')
        ordering = ['-date_creation']
    
    def __str__(self):
        """Représentation string de la réinitialisation."""
        return f"{self.utilisateur.username} - {self.statut}"
    
    def save(self, *args, **kwargs):
        """Sauvegarde avec génération automatique du token et de l'expiration."""
        if not self.token:
            self.token = self.generate_token()
        
        if not self.date_expiration:
            # Token valide 1 heure
            self.date_expiration = timezone.now() + timedelta(hours=1)
        
        super().save(*args, **kwargs)
    
    @staticmethod
    def generate_token():
        """Génère un token sécurisé."""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(64))
    
    def is_valid(self):
        """Vérifie si le token est valide."""
        return (
            self.statut == 'ACTIF' and
            timezone.now() < self.date_expiration
        )
    
    def use_token(self, ip_address):
        """Marque le token comme utilisé."""
        self.statut = 'UTILISE'
        self.date_utilisation = timezone.now()
        self.adresse_ip_utilisation = ip_address
        self.save()
    
    def expire_token(self):
        """Marque le token comme expiré."""
        self.statut = 'EXPIRE'
        self.save()


class EmailVerification(models.Model):
    """
    Modèle pour la vérification des adresses email.
    
    Gère les codes de vérification envoyés par email
    lors de l'inscription ou du changement d'email.
    """
    
    STATUT_CHOICES = [
        ('EN_ATTENTE', _('En attente')),
        ('VERIFIE', _('Vérifié')),
        ('EXPIRE', _('Expiré')),
        ('ANNULE', _('Annulé')),
    ]
    
    TYPE_CHOICES = [
        ('INSCRIPTION', _('Inscription')),
        ('CHANGEMENT_EMAIL', _('Changement d\'email')),
        ('REACTIVATION', _('Réactivation de compte')),
    ]
    
    utilisateur = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='email_verifications',
        verbose_name=_('Utilisateur'),
        help_text="Utilisateur concerné"
    )
    
    email = models.EmailField(
        _('Email'),
        help_text="Adresse email à vérifier"
    )
    
    code = models.CharField(
        _('Code de vérification'),
        max_length=6,
        help_text="Code de vérification à 6 chiffres"
    )
    
    type_verification = models.CharField(
        _('Type de vérification'),
        max_length=20,
        choices=TYPE_CHOICES,
        default='INSCRIPTION',
        help_text="Type de vérification"
    )
    
    statut = models.CharField(
        _('Statut'),
        max_length=15,
        choices=STATUT_CHOICES,
        default='EN_ATTENTE',
        help_text="Statut de la vérification"
    )
    
    # Dates
    date_creation = models.DateTimeField(
        _('Date de création'),
        auto_now_add=True,
        help_text="Date de création du code"
    )
    
    date_expiration = models.DateTimeField(
        _('Date d\'expiration'),
        help_text="Date d'expiration du code"
    )
    
    date_verification = models.DateTimeField(
        _('Date de vérification'),
        null=True,
        blank=True,
        help_text="Date de vérification réussie"
    )
    
    # Sécurité
    tentatives = models.PositiveIntegerField(
        _('Tentatives'),
        default=0,
        help_text="Nombre de tentatives de vérification"
    )
    
    max_tentatives = models.PositiveIntegerField(
        _('Tentatives maximum'),
        default=3,
        help_text="Nombre maximum de tentatives autorisées"
    )
    
    adresse_ip = models.GenericIPAddressField(
        _('Adresse IP'),
        null=True,
        blank=True,
        help_text="Adresse IP de création"
    )
    
    class Meta:
        verbose_name = _('Vérification d\'email')
        verbose_name_plural = _('Vérifications d\'email')
        ordering = ['-date_creation']
    
    def __str__(self):
        """Représentation string de la vérification."""
        return f"{self.utilisateur.username} - {self.email} ({self.statut})"
    
    def save(self, *args, **kwargs):
        """Sauvegarde avec génération automatique du code et de l'expiration."""
        if not self.code:
            self.code = self.generate_code()
        
        if not self.date_expiration:
            # Code valide 15 minutes
            from django.conf import settings
            validity_minutes = settings.SPOTVIBE_SETTINGS.get('VERIFICATION_CODE_VALIDITY', 15)
            self.date_expiration = timezone.now() + timedelta(minutes=validity_minutes)
        
        super().save(*args, **kwargs)
    
    @staticmethod
    def generate_code():
        """Génère un code de vérification à 6 chiffres."""
        return ''.join(secrets.choice(string.digits) for _ in range(6))
    
    def is_valid(self):
        """Vérifie si le code est valide."""
        return (
            self.statut == 'EN_ATTENTE' and
            timezone.now() < self.date_expiration and
            self.tentatives < self.max_tentatives
        )
    
    def verify_code(self, code_input):
        """Vérifie le code saisi."""
        self.tentatives += 1
        
        if not self.is_valid():
            return False
        
        if self.code == code_input:
            self.statut = 'VERIFIE'
            self.date_verification = timezone.now()
            self.save()
            return True
        else:
            # Marquer comme expiré si trop de tentatives
            if self.tentatives >= self.max_tentatives:
                self.statut = 'EXPIRE'
            self.save()
            return False
    
    def resend_code(self):
        """Génère un nouveau code pour renvoyer."""
        if self.statut in ['EN_ATTENTE', 'EXPIRE']:
            self.code = self.generate_code()
            self.date_creation = timezone.now()
            self.date_expiration = timezone.now() + timedelta(minutes=15)
            self.statut = 'EN_ATTENTE'
            self.tentatives = 0
            self.save()
            return True
        return False


class TwoFactorAuth(models.Model):
    """
    Modèle pour l'authentification à deux facteurs.
    
    Gère les paramètres et codes de l'authentification 2FA
    pour renforcer la sécurité des comptes.
    """
    
    METHODE_CHOICES = [
        ('SMS', _('SMS')),
        ('EMAIL', _('Email')),
        ('TOTP', _('Application d\'authentification')),
    ]
    
    utilisateur = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='two_factor_auth',
        verbose_name=_('Utilisateur'),
        help_text="Utilisateur concerné"
    )
    
    actif = models.BooleanField(
        _('Actif'),
        default=False,
        help_text="Authentification 2FA activée"
    )
    
    methode = models.CharField(
        _('Méthode'),
        max_length=10,
        choices=METHODE_CHOICES,
        default='SMS',
        help_text="Méthode d'authentification 2FA"
    )
    
    # Pour TOTP (Time-based One-Time Password)
    secret_key = models.CharField(
        _('Clé secrète'),
        max_length=32,
        blank=True,
        help_text="Clé secrète pour TOTP"
    )
    
    # Codes de récupération
    codes_recuperation = models.JSONField(
        _('Codes de récupération'),
        default=list,
        blank=True,
        help_text="Codes de récupération d'urgence"
    )
    
    # Statistiques
    derniere_utilisation = models.DateTimeField(
        _('Dernière utilisation'),
        null=True,
        blank=True,
        help_text="Dernière utilisation de 2FA"
    )
    
    date_activation = models.DateTimeField(
        _('Date d\'activation'),
        null=True,
        blank=True,
        help_text="Date d'activation de 2FA"
    )
    
    class Meta:
        verbose_name = _('Authentification à deux facteurs')
        verbose_name_plural = _('Authentifications à deux facteurs')
    
    def __str__(self):
        """Représentation string de 2FA."""
        status = "Activé" if self.actif else "Désactivé"
        return f"{self.utilisateur.username} - 2FA {status}"
    
    def generate_recovery_codes(self, count=10):
        """Génère des codes de récupération."""
        codes = []
        for _ in range(count):
            code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
            codes.append(code)
        
        self.codes_recuperation = codes
        self.save()
        return codes
    
    def use_recovery_code(self, code):
        """Utilise un code de récupération."""
        if code in self.codes_recuperation:
            self.codes_recuperation.remove(code)
            self.save()
            return True
        return False

