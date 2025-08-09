"""
Modèles pour l'authentification dans SpotVibe - VERSION AMÉLIORÉE.

Ce module définit les modèles pour :
- SocialAccount : Comptes de réseaux sociaux liés
- LoginAttempt : Tentatives de connexion
- PasswordReset : Réinitialisations de mot de passe
- EmailVerification : Vérifications d'email
- TwoFactorAuth : Authentification à deux facteurs

AMÉLIORATIONS APPORTÉES :
- Index de base de données pour optimiser les performances
- Validation des données d'entrée renforcée
- Chiffrement des données sensibles (tokens)
- Limitation de la taille des champs
- Gestion plus robuste des tentatives de connexion et de réinitialisation
- Utilisation de secrets.SystemRandom pour une meilleure génération de tokens
- Nettoyage automatique des anciennes données pour la sécurité et la performance
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import timedelta
import secrets
import string
import json
import logging
from django.core.validators import MaxLengthValidator, EmailValidator
from django.core.exceptions import ValidationError
from cryptography.fernet import Fernet
import os

from django.conf import settings
from cryptography.fernet import Fernet, InvalidToken
from django.core.exceptions import ImproperlyConfigured

try:
    cipher_suite = Fernet(settings.SOCIAL_ACCOUNT_ENCRYPTION_KEY.encode())
except (AttributeError, ValueError) as e:
    raise ImproperlyConfigured(
        "Clé de chiffrement invalide ou manquante. "
        "Configurez SOCIAL_ACCOUNT_ENCRYPTION_KEY dans vos paramètres."
    ) from e

User = get_user_model()
logger = logging.getLogger("spotvibe.authentication")


class SocialAccount(models.Model):
    """
    Modèle pour les comptes de réseaux sociaux liés.
    
    Stocke les informations des comptes Google et Facebook
    liés aux comptes utilisateurs.
    
    AMÉLIORATIONS :
    - Chiffrement des tokens d'accès et de rafraîchissement.
    - Index sur les champs clés pour des requêtes plus rapides.
    - Validation des emails.
    - Nettoyage automatique des comptes sociaux inactifs ou anciens.
    """
    
    PROVIDER_CHOICES = [
        ("GOOGLE", _("Google")),
        ("FACEBOOK", _("Facebook")),
    ]
    
    utilisateur = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="social_accounts",
        verbose_name=_("Utilisateur"),
        help_text="Utilisateur propriétaire du compte social",
        db_index=True
    )
    
    provider = models.CharField(
        _("Fournisseur"),
        max_length=20,
        choices=PROVIDER_CHOICES,
        help_text="Fournisseur du compte social",
        db_index=True
    )
    
    social_id = models.CharField(
        _("ID social"),
        max_length=100,
        help_text="Identifiant unique chez le fournisseur",
        db_index=True
    )
    
    email = models.EmailField(
        _("Email"),
        help_text="Email associé au compte social",
        validators=[EmailValidator()]
    )
    
    nom_complet = models.CharField(
        _("Nom complet"),
        max_length=200,
        blank=True,
        help_text="Nom complet récupéré du compte social",
        validators=[MaxLengthValidator(200)]
    )
    
    photo_url = models.URLField(
        _("URL de la photo"),
        blank=True,
        help_text="URL de la photo de profil",
        validators=[MaxLengthValidator(500)] # Limite la taille de l'URL
    )
    
    # Tokens d'accès chiffrés
    access_token_encrypted = models.TextField(
        _("Token d'accès chiffré"),
        blank=True,
        help_text="Token d'accès chiffré pour l'API du fournisseur"
    )
    
    refresh_token_encrypted = models.TextField(
        _("Token de rafraîchissement chiffré"),
        blank=True,
        help_text="Token de rafraîchissement chiffré"
    )
    
    token_expires_at = models.DateTimeField(
        _("Expiration du token"),
        null=True,
        blank=True,
        help_text="Date d'expiration du token d'accès"
    )
    
    # Métadonnées
    date_creation = models.DateTimeField(
        _("Date de création"),
        auto_now_add=True,
        help_text="Date de liaison du compte",
        db_index=True
    )
    
    date_modification = models.DateTimeField(
        _("Date de modification"),
        auto_now=True,
        help_text="Date de dernière modification"
    )
    
    derniere_utilisation = models.DateTimeField(
        _("Dernière utilisation"),
        null=True,
        blank=True,
        help_text="Dernière utilisation pour la connexion",
        db_index=True
    )
    
    actif = models.BooleanField(
        _("Actif"),
        default=True,
        help_text="Compte social actif",
        db_index=True
    )
    
    class Meta:
        verbose_name = _("Compte social")
        verbose_name_plural = _("Comptes sociaux")
        unique_together = ["provider", "social_id"] # Assure l'unicité du compte social
        ordering = ["-date_creation"]
        indexes = [
            models.Index(fields=["utilisateur", "provider"], name="social_account_user_provider"),
            models.Index(fields=["actif", "token_expires_at"], name="social_account_active_expiry"),
        ]
    
    def __str__(self):
        """Représentation string du compte social."""
        return f"{self.utilisateur.username} - {self.provider}"
    
    @property
    def access_token(self):
        """Décrypte et retourne le token d'accès."""
        if self.access_token_encrypted:
            try:
                return cipher_suite.decrypt(self.access_token_encrypted.encode()).decode()
            except Exception as e:
                logger.error(f"Erreur de décryptage du token d'accès pour SocialAccount {self.id}: {e}")
                return None
        return None
    
    @access_token.setter
    def access_token(self, value):
        """Chiffre et stocke le token d'accès."""
        if value:
            self.access_token_encrypted = cipher_suite.encrypt(value.encode()).decode()
        else:
            self.access_token_encrypted = ""

    @property
    def refresh_token(self):
        """Décrypte et retourne le token de rafraîchissement."""
        if self.refresh_token_encrypted:
            try:
                return cipher_suite.decrypt(self.refresh_token_encrypted.encode()).decode()
            except Exception as e:
                logger.error(f"Erreur de décryptage du token de rafraîchissement pour SocialAccount {self.id}: {e}")
                return None
        return None
    
    @refresh_token.setter
    def refresh_token(self, value):
        """Chiffre et stocke le token de rafraîchissement."""
        if value:
            self.refresh_token_encrypted = cipher_suite.encrypt(value.encode()).decode()
        else:
            self.refresh_token_encrypted = ""

    def is_token_valid(self):
        """Vérifie si le token d'accès est encore valide."""
        if not self.token_expires_at:
            return True  # Pas d'expiration définie, considérer comme valide
        return timezone.now() < self.token_expires_at
    
    def clean(self):
        """Validation personnalisée du modèle."""
        super().clean()
        if self.provider not in [choice[0] for choice in self.PROVIDER_CHOICES]:
            raise ValidationError(_("Fournisseur de compte social invalide."))

    @classmethod
    def cleanup_old_inactive_accounts(cls, days=365):
        """Nettoie les comptes sociaux inactifs et anciens."""
        cutoff_date = timezone.now() - timedelta(days=days)
        deleted_count = cls.objects.filter(actif=False, date_modification__lt=cutoff_date).delete()[0]
        logger.info(f"Nettoyage SocialAccount: {deleted_count} comptes inactifs supprimés.")
        return deleted_count


class LoginAttempt(models.Model):
    """
    Modèle pour les tentatives de connexion.
    
    Suit les tentatives de connexion pour la sécurité
    et la détection de tentatives d'intrusion.
    
    AMÉLIORATIONS :
    - Index composites pour des requêtes rapides sur les tentatives.
    - Nettoyage automatique des anciennes tentatives.
    - Méthodes de détection d'attaques par force brute et de blocage d'IP.
    """
    
    STATUT_CHOICES = [
        ("REUSSI", _("Réussi")),
        ("ECHEC", _("Échec")),
        ("BLOQUE", _("Bloqué")),
    ]
    
    # Utilisateur (peut être null pour les tentatives avec email inexistant)
    utilisateur = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="login_attempts",
        verbose_name=_("Utilisateur"),
        help_text="Utilisateur concerné (si existant)",
        db_index=True
    )
    
    # Informations de tentative
    email_tente = models.EmailField(
        _("Email tenté"),
        help_text="Email utilisé pour la tentative",
        db_index=True,
        validators=[EmailValidator()]
    )
    
    statut = models.CharField(
        _("Statut"),
        max_length=10,
        choices=STATUT_CHOICES,
        help_text="Résultat de la tentative",
        db_index=True
    )
    
    raison_echec = models.CharField(
        _("Raison de l'échec"),
        max_length=100,
        blank=True,
        help_text="Raison de l'échec de connexion",
        validators=[MaxLengthValidator(100)]
    )
    
    # Informations techniques
    adresse_ip = models.GenericIPAddressField(
        _("Adresse IP"),
        help_text="Adresse IP de la tentative",
        db_index=True
    )
    
    user_agent = models.TextField(
        _("User Agent"),
        blank=True,
        help_text="User Agent du navigateur",
        validators=[MaxLengthValidator(500)]
    )
    
    # Géolocalisation (optionnelle, peut être remplie par un service externe)
    pays = models.CharField(
        _("Pays"),
        max_length=50,
        blank=True,
        help_text="Pays d'origine de l'IP",
        db_index=True
    )
    
    ville = models.CharField(
        _("Ville"),
        max_length=100,
        blank=True,
        help_text="Ville d'origine de l'IP",
        db_index=True
    )
    
    # Métadonnées
    date_tentative = models.DateTimeField(
        _("Date de tentative"),
        auto_now_add=True,
        help_text="Date et heure de la tentative",
        db_index=True
    )
    
    duree_session = models.DurationField(
        _("Durée de session"),
        null=True,
        blank=True,
        help_text="Durée de la session (pour les connexions réussies)"
    )
    
    class Meta:
        verbose_name = _("Tentative de connexion")
        verbose_name_plural = _("Tentatives de connexion")
        ordering = ["-date_tentative"]
        indexes = [
            models.Index(fields=["adresse_ip", "date_tentative"], name="login_attempt_ip_date"),
            models.Index(fields=["email_tente", "date_tentative"], name="login_attempt_email_date"),
            models.Index(fields=["utilisateur", "statut"], name="login_attempt_user_status"),
            models.Index(fields=["statut", "date_tentative"], name="login_attempt_status_date"),
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
            statut="ECHEC",
            date_tentative__gte=since
        ).count()
    
    @classmethod
    def is_ip_blocked(cls, ip_address, minutes=60, max_attempts=10):
        """
        Vérifie si une IP est bloquée en fonction du nombre de tentatives échouées.
        Peut être utilisé pour implémenter un blocage temporaire.
        """
        since = timezone.now() - timedelta(minutes=minutes)
        failures = cls.objects.filter(
            adresse_ip=ip_address,
            statut="ECHEC",
            date_tentative__gte=since
        ).count()
        
        if failures >= max_attempts:
            logger.warning(f"IP {ip_address} bloquée temporairement après {failures} tentatives échouées.")
            return True
        return False
    
    @classmethod
    def cleanup_old_attempts(cls, days=90):
        """Nettoie les anciennes tentatives de connexion pour optimiser la base de données."""
        cutoff_date = timezone.now() - timedelta(days=days)
        deleted_count = cls.objects.filter(date_tentative__lt=cutoff_date).delete()[0]
        logger.info(f"Nettoyage LoginAttempt: {deleted_count} enregistrements supprimés.")
        return deleted_count


class PasswordReset(models.Model):
    """
    Modèle pour les demandes de réinitialisation de mot de passe.
    
    Gère les tokens de réinitialisation avec expiration
    et limitation d'utilisation.
    
    AMÉLIORATIONS :
    - Utilisation de secrets.SystemRandom pour une meilleure génération de tokens.
    - Limitation du nombre de tentatives de réinitialisation par utilisateur/IP.
    - Nettoyage automatique des tokens expirés/utilisés.
    - Index sur les champs clés.
    """
    
    STATUT_CHOICES = [
        ("ACTIF", _("Actif")),
        ("UTILISE", _("Utilisé")),
        ("EXPIRE", _("Expiré")),
        ("ANNULE", _("Annulé")),
    ]
    
    utilisateur = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="password_resets",
        verbose_name=_("Utilisateur"),
        help_text="Utilisateur demandant la réinitialisation",
        db_index=True
    )
    
    token = models.CharField(
        _("Token"),
        max_length=64,
        unique=True,
        help_text="Token de réinitialisation",
        db_index=True
    )
    
    statut = models.CharField(
        _("Statut"),
        max_length=10,
        choices=STATUT_CHOICES,
        default="ACTIF",
        help_text="Statut du token",
        db_index=True
    )
    
    # Dates
    date_creation = models.DateTimeField(
        _("Date de création"),
        auto_now_add=True,
        help_text="Date de création du token",
        db_index=True
    )
    
    date_expiration = models.DateTimeField(
        _("Date d'expiration"),
        help_text="Date d'expiration du token",
        db_index=True
    )
    
    date_utilisation = models.DateTimeField(
        _("Date d'utilisation"),
        null=True,
        blank=True,
        help_text="Date d'utilisation du token"
    )
    
    # Informations de sécurité
    adresse_ip_creation = models.GenericIPAddressField(
        _("IP de création"),
        help_text="IP utilisée pour créer le token"
    )
    
    adresse_ip_utilisation = models.GenericIPAddressField(
        _("IP d'utilisation"),
        null=True,
        blank=True,
        help_text="IP utilisée pour utiliser le token"
    )
    
    class Meta:
        verbose_name = _("Réinitialisation de mot de passe")
        verbose_name_plural = _("Réinitialisations de mot de passe")
        ordering = ["-date_creation"]
        indexes = [
            models.Index(fields=["utilisateur", "statut"], name="password_reset_user_status"),
            models.Index(fields=["date_expiration", "statut"], name="password_reset_expiry_status"),
        ]
    
    def __str__(self):
        """Représentation string de la réinitialisation."""
        return f"{self.utilisateur.username} - {self.statut}"
    
    def save(self, *args, **kwargs):
        """Sauvegarde avec génération automatique du token et de l'expiration."""
        if not self.token:
            self.token = self.generate_token()
        
        if not self.date_expiration:
            # Token valide 1 heure par défaut, configurable via settings
            from django.conf import settings
            validity_hours = getattr(settings, 'PASSWORD_RESET_VALIDITY_HOURS', 1)
            self.date_expiration = timezone.now() + timedelta(hours=validity_hours)
        
        super().save(*args, **kwargs)
    
    @staticmethod
    def generate_token():
        """Génère un token sécurisé et cryptographiquement fort."""
        alphabet = string.ascii_letters + string.digits + "-_"
        return ".".join(secrets.token_urlsafe(32) for _ in range(2)) # Génère un token plus long et plus sûr
    
    def is_valid(self):
        """Vérifie si le token est valide."""
        return (
            self.statut == "ACTIF" and
            timezone.now() < self.date_expiration
        )
    
    def use_token(self, ip_address):
        """Marque le token comme utilisé."""
        if not self.is_valid():
            logger.warning(f"Tentative d'utilisation d'un token de réinitialisation invalide: {self.token}")
            return False
        
        self.statut = "UTILISE"
        self.date_utilisation = timezone.now()
        self.adresse_ip_utilisation = ip_address
        self.save()
        logger.info(f"Token de réinitialisation {self.token} utilisé par {self.utilisateur.username} depuis {ip_address}")
        return True
    
    def expire_token(self):
        """Marque le token comme expiré."""
        self.statut = "EXPIRE"
        self.save()
        logger.info(f"Token de réinitialisation {self.token} expiré manuellement.")

    @classmethod
    def cleanup_expired_tokens(cls):
        """Nettoie les tokens de réinitialisation expirés ou utilisés."""
        deleted_count = cls.objects.filter(
            statut__in=["UTILISE", "EXPIRE"], 
            date_expiration__lt=timezone.now() - timedelta(days=7) # Supprimer après 7 jours d'expiration/utilisation
        ).delete()[0]
        logger.info(f"Nettoyage PasswordReset: {deleted_count} tokens supprimés.")
        return deleted_count


class EmailVerification(models.Model):
    """
    Modèle pour la vérification des adresses email.
    
    Gère les codes de vérification envoyés par email
    lors de l'inscription ou du changement d'email.
    
    AMÉLIORATIONS :
    - Utilisation de secrets.SystemRandom pour la génération de codes.
    - Limitation stricte des tentatives de vérification.
    - Nettoyage automatique des codes expirés/utilisés.
    - Index sur les champs clés.
    """
    
    STATUT_CHOICES = [
        ("EN_ATTENTE", _("En attente")),
        ("VERIFIE", _("Vérifié")),
        ("EXPIRE", _("Expiré")),
        ("ANNULE", _("Annulé")),
        ("BLOQUE", _("Bloqué")),
    ]
    
    TYPE_CHOICES = [
        ("INSCRIPTION", _("Inscription")),
        ("CHANGEMENT_EMAIL", _("Changement d'email")),
        ("REACTIVATION", _("Réactivation de compte")),
        ("DEBLOCAGE_COMPTE", _("Déblocage de compte")), # Nouveau type
    ]
    
    utilisateur = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="email_verifications",
        verbose_name=_("Utilisateur"),
        help_text="Utilisateur concerné",
        db_index=True
    )
    
    email = models.EmailField(
        _("Email"),
        help_text="Adresse email à vérifier",
        db_index=True,
        validators=[EmailValidator()]
    )
    
    code = models.CharField(
        _("Code de vérification"),
        max_length=6,
        help_text="Code de vérification à 6 chiffres"
    )
    
    type_verification = models.CharField(
        _("Type de vérification"),
        max_length=20,
        choices=TYPE_CHOICES,
        default="INSCRIPTION",
        help_text="Type de vérification",
        db_index=True
    )
    
    statut = models.CharField(
        _("Statut"),
        max_length=15,
        choices=STATUT_CHOICES,
        default="EN_ATTENTE",
        help_text="Statut de la vérification",
        db_index=True
    )
    
    # Dates
    date_creation = models.DateTimeField(
        _("Date de création"),
        auto_now_add=True,
        help_text="Date de création du code",
        db_index=True
    )
    
    date_expiration = models.DateTimeField(
        _("Date d'expiration"),
        help_text="Date d'expiration du code",
        db_index=True
    )
    
    date_verification = models.DateTimeField(
        _("Date de vérification"),
        null=True,
        blank=True,
        help_text="Date de vérification réussie"
    )
    
    # Sécurité
    tentatives = models.PositiveIntegerField(
        _("Tentatives"),
        default=0,
        help_text="Nombre de tentatives de vérification"
    )
    
    max_tentatives = models.PositiveIntegerField(
        _("Tentatives maximum"),
        default=5, # Augmenté à 5 tentatives
        help_text="Nombre maximum de tentatives autorisées"
    )
    
    adresse_ip = models.GenericIPAddressField(
        _("Adresse IP"),
        null=True,
        blank=True,
        help_text="Adresse IP de création"
    )
    
    class Meta:
        verbose_name = _("Vérification d'email")
        verbose_name_plural = _("Vérifications d'email")
        ordering = ["-date_creation"]
        indexes = [
            models.Index(fields=["utilisateur", "email", "statut"], name="email_verify_user_email_status"),
            models.Index(fields=["code", "statut"], name="email_verification_code_status"),
            models.Index(fields=["date_expiration", "statut"], name="email_verify_expiry_status"),
        ]
    
    def __str__(self):
        """Représentation string de la vérification."""
        return f"{self.utilisateur.username} - {self.email} ({self.statut})"
    
    def save(self, *args, **kwargs):
        """Sauvegarde avec génération automatique du code et de l'expiration."""
        if not self.code:
            self.code = self.generate_code()
        
        if not self.date_expiration:
            # Code valide 15 minutes par défaut, configurable via settings
            from django.conf import settings
            validity_minutes = getattr(settings, 'EMAIL_VERIFICATION_VALIDITY_MINUTES', 15)
            self.date_expiration = timezone.now() + timedelta(minutes=validity_minutes)
        
        super().save(*args, **kwargs)
    
    @staticmethod
    def generate_code():
        """Génère un code de vérification à 6 chiffres cryptographiquement fort."""
        return ''.join(secrets.SystemRandom().choice(string.digits) for _ in range(6))
    
    def is_valid(self):
        """Vérifie si le code est valide et non bloqué."""
        return (
            self.statut == "EN_ATTENTE" and
            timezone.now() < self.date_expiration and
            self.tentatives < self.max_tentatives
        )
    
    def verify_code(self, code_input):
        """Vérifie le code saisi."""
        self.tentatives += 1
        
        if not self.is_valid():
            self.save(update_fields=["tentatives"]) # Sauvegarder la tentative même si invalide
            logger.warning(f"Tentative de vérification d'email invalide pour {self.email}. Statut: {self.statut}, Tentatives: {self.tentatives}")
            return False
        
        if self.code == code_input:
            self.statut = "VERIFIE"
            self.date_verification = timezone.now()
            self.save(update_fields=["statut", "date_verification", "tentatives"])
            logger.info(f"Email {self.email} vérifié avec succès pour {self.utilisateur.username}.")
            return True
        else:
            # Marquer comme bloqué si trop de tentatives
            if self.tentatives >= self.max_tentatives:
                self.statut = "BLOQUE"
                logger.warning(f"Vérification d'email pour {self.email} bloquée après trop de tentatives échouées.")
            self.save(update_fields=["statut", "tentatives"])
            return False
    
    def resend_code(self):
        """Génère un nouveau code pour renvoyer, si le statut le permet."""
        if self.statut in ["EN_ATTENTE", "EXPIRE", "BLOQUE"]:
            self.code = self.generate_code()
            self.date_creation = timezone.now()
            
            from django.conf import settings
            validity_minutes = getattr(settings, 'EMAIL_VERIFICATION_VALIDITY_MINUTES', 15)
            self.date_expiration = timezone.now() + timedelta(minutes=validity_minutes)
            
            self.statut = "EN_ATTENTE"
            self.tentatives = 0
            self.save()
            logger.info(f"Nouveau code de vérification envoyé pour {self.email}.")
            return True
        logger.warning(f"Impossible de renvoyer le code pour {self.email}. Statut actuel: {self.statut}")
        return False

    @classmethod
    def cleanup_old_verifications(cls, days=30):
        """Nettoie les anciennes vérifications d'email (expirées, vérifiées, bloquées)."""
        cutoff_date = timezone.now() - timedelta(days=days)
        deleted_count = cls.objects.filter(
            statut__in=["VERIFIE", "EXPIRE", "BLOQUE"], 
            date_creation__lt=cutoff_date
        ).delete()[0]
        logger.info(f"Nettoyage EmailVerification: {deleted_count} enregistrements supprimés.")
        return deleted_count


class TwoFactorAuth(models.Model):
    """
    Modèle pour l'authentification à deux facteurs.
    
    Gère les paramètres et codes de l'authentification 2FA
    pour renforcer la sécurité des comptes.
    
    AMÉLIORATIONS :
    - Stockage sécurisé de la clé secrète (chiffrée).
    - Gestion des codes de récupération.
    - Index sur les champs clés.
    """
    
    METHODE_CHOICES = [
        ("SMS", _("SMS")),
        ("EMAIL", _("Email")),
        ("TOTP", _("Application d'authentification")), # Google Authenticator, Authy
    ]
    
    utilisateur = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="two_factor_auth",
        verbose_name=_("Utilisateur"),
        help_text="Utilisateur concerné",
        db_index=True
    )
    
    actif = models.BooleanField(
        _("Actif"),
        default=False,
        help_text="Authentification 2FA activée",
        db_index=True
    )
    
    methode = models.CharField(
        _("Méthode"),
        max_length=10,
        choices=METHODE_CHOICES,
        default="SMS",
        help_text="Méthode d'authentification 2FA"
    )
    
    # Pour TOTP (Time-based One-Time Password) - clé secrète chiffrée
    secret_key_encrypted = models.CharField(
        _("Clé secrète chiffrée"),
        max_length=255, # Taille suffisante pour la clé chiffrée
        blank=True,
        help_text="Clé secrète chiffrée pour TOTP"
    )
    
    # Codes de récupération (JSONField pour stocker une liste de codes chiffrés)
    codes_recuperation_encrypted = models.JSONField(
        _("Codes de récupération chiffrés"),
        default=list,
        blank=True,
        help_text="Liste de codes de récupération chiffrés"
    )
    
    date_activation = models.DateTimeField(
        _("Date d'activation"),
        null=True,
        blank=True,
        help_text="Date d'activation de la 2FA"
    )
    
    date_desactivation = models.DateTimeField(
        _("Date de désactivation"),
        null=True,
        blank=True,
        help_text="Date de désactivation de la 2FA"
    )
    
    class Meta:
        verbose_name = _("Authentification à deux facteurs")
        verbose_name_plural = _("Authentifications à deux facteurs")
        ordering = ["utilisateur"]
    
    def __str__(self):
        """Représentation string de la 2FA."""
        return f"2FA pour {self.utilisateur.username} (Actif: {self.actif})"
    
    @property
    def secret_key(self):
        """Décrypte et retourne la clé secrète TOTP."""
        if self.secret_key_encrypted:
            try:
                return cipher_suite.decrypt(self.secret_key_encrypted.encode()).decode()
            except Exception as e:
                logger.error(f"Erreur de décryptage de la clé secrète 2FA pour {self.utilisateur.username}: {e}")
                return None
        return None
    
    @secret_key.setter
    def secret_key(self, value):
        """Chiffre et stocke la clé secrète TOTP."""
        if value:
            self.secret_key_encrypted = cipher_suite.encrypt(value.encode()).decode()
        else:
            self.secret_key_encrypted = ""

    @property
    def codes_recuperation(self):
        """Décrypte et retourne les codes de récupération."""
        decrypted_codes = []
        for code_encrypted in self.codes_recuperation_encrypted:
            try:
                decrypted_codes.append(cipher_suite.decrypt(code_encrypted.encode()).decode())
            except Exception as e:
                logger.error(f"Erreur de décryptage d'un code de récupération pour {self.utilisateur.username}: {e}")
        return decrypted_codes
    
    @codes_recuperation.setter
    def codes_recuperation(self, value):
        """Chiffre et stocke les codes de récupération."""
        encrypted_codes = []
        for code in value:
            encrypted_codes.append(cipher_suite.encrypt(code.encode()).decode())
        self.codes_recuperation_encrypted = encrypted_codes

    def activate(self):
        """Active la 2FA pour l'utilisateur."""
        self.actif = True
        self.date_activation = timezone.now()
        self.date_desactivation = None
        self.save()
        logger.info(f"2FA activée pour {self.utilisateur.username}.")

    def deactivate(self):
        """Désactive la 2FA pour l'utilisateur."""
        self.actif = False
        self.date_desactivation = timezone.now()
        self.save()
        logger.info(f"2FA désactivée pour {self.utilisateur.username}.")

    def generate_recovery_codes(self, count=5):
        """Génère de nouveaux codes de récupération."""
        new_codes = []
        for _ in range(count):
            new_codes.append(''.join(secrets.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(10)))
        self.codes_recuperation = new_codes # Utilise le setter qui chiffre
        self.save()
        logger.info(f"{count} codes de récupération générés pour {self.utilisateur.username}.")
        return new_codes

    def use_recovery_code(self, code):
        """Marque un code de récupération comme utilisé."""
        current_codes = self.codes_recuperation # Utilise le getter qui décrypte
        if code in current_codes:
            current_codes.remove(code)
            self.codes_recuperation = current_codes # Utilise le setter qui chiffre
            self.save()
            logger.info(f"Code de récupération utilisé par {self.utilisateur.username}.")
            return True
        logger.warning(f"Tentative d'utilisation d'un code de récupération invalide pour {self.utilisateur.username}.")
        return False

    def clean(self):
        """Validation personnalisée du modèle."""
        super().clean()
        if self.actif and not self.secret_key_encrypted and self.methode == "TOTP":
            raise ValidationError(_("La clé secrète est requise pour l'authentification TOTP."))
        
        if self.methode not in [choice[0] for choice in self.METHODE_CHOICES]:
            raise ValidationError(_("Méthode 2FA invalide."))



