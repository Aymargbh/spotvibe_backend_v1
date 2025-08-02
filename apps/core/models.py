"""
Modèles core pour SpotVibe.

Ce module définit les modèles utilitaires et de configuration :
- AppSettings : Configuration de l'application
- AuditLog : Logs d'audit des actions
- ContactMessage : Messages de contact
- FAQ : Questions fréquemment posées
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

User = get_user_model()


class AppSettings(models.Model):
    """
    Modèle pour les paramètres de configuration de l'application.
    
    Permet de stocker des paramètres configurables sans redéploiement.
    """
    
    TYPE_CHOICES = [
        ('STRING', _('Chaîne de caractères')),
        ('INTEGER', _('Nombre entier')),
        ('FLOAT', _('Nombre décimal')),
        ('BOOLEAN', _('Booléen')),
        ('JSON', _('JSON')),
    ]
    
    cle = models.CharField(
        _('Clé'),
        max_length=100,
        unique=True,
        help_text="Clé unique du paramètre"
    )
    
    valeur = models.TextField(
        _('Valeur'),
        help_text="Valeur du paramètre"
    )
    
    type_valeur = models.CharField(
        _('Type de valeur'),
        max_length=10,
        choices=TYPE_CHOICES,
        default='STRING',
        help_text="Type de données de la valeur"
    )
    
    description = models.TextField(
        _('Description'),
        help_text="Description du paramètre"
    )
    
    categorie = models.CharField(
        _('Catégorie'),
        max_length=50,
        default='GENERAL',
        help_text="Catégorie du paramètre"
    )
    
    modifiable = models.BooleanField(
        _('Modifiable'),
        default=True,
        help_text="Paramètre modifiable via l'interface admin"
    )
    
    date_creation = models.DateTimeField(
        _('Date de création'),
        auto_now_add=True,
        help_text="Date de création du paramètre"
    )
    
    date_modification = models.DateTimeField(
        _('Date de modification'),
        auto_now=True,
        help_text="Date de dernière modification"
    )
    
    class Meta:
        verbose_name = _('Paramètre d\'application')
        verbose_name_plural = _('Paramètres d\'application')
        ordering = ['categorie', 'cle']
    
    def __str__(self):
        """Représentation string du paramètre."""
        return f"{self.cle} = {self.valeur}"
    
    def get_typed_value(self):
        """Retourne la valeur convertie selon son type."""
        if self.type_valeur == 'INTEGER':
            return int(self.valeur)
        elif self.type_valeur == 'FLOAT':
            return float(self.valeur)
        elif self.type_valeur == 'BOOLEAN':
            return self.valeur.lower() in ('true', '1', 'yes', 'on')
        elif self.type_valeur == 'JSON':
            import json
            return json.loads(self.valeur)
        else:
            return self.valeur


class AuditLog(models.Model):
    """
    Modèle pour les logs d'audit des actions importantes.
    
    Enregistre toutes les actions sensibles pour la traçabilité
    et la sécurité.
    """
    
    ACTION_CHOICES = [
        ('CREATE', _('Création')),
        ('UPDATE', _('Modification')),
        ('DELETE', _('Suppression')),
        ('LOGIN', _('Connexion')),
        ('LOGOUT', _('Déconnexion')),
        ('APPROVE', _('Approbation')),
        ('REJECT', _('Rejet')),
        ('PAYMENT', _('Paiement')),
        ('REFUND', _('Remboursement')),
        ('EXPORT', _('Export')),
        ('IMPORT', _('Import')),
        ('CONFIG', _('Configuration')),
    ]
    
    # Utilisateur qui a effectué l'action
    utilisateur = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
        verbose_name=_('Utilisateur'),
        help_text="Utilisateur qui a effectué l'action"
    )
    
    # Action effectuée
    action = models.CharField(
        _('Action'),
        max_length=20,
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
    adresse_ip = models.GenericIPAddressField(
        _('Adresse IP'),
        null=True,
        blank=True,
        help_text="Adresse IP de l'utilisateur"
    )
    
    user_agent = models.TextField(
        _('User Agent'),
        blank=True,
        help_text="User Agent du navigateur"
    )
    
    donnees_avant = models.JSONField(
        _('Données avant'),
        default=dict,
        blank=True,
        help_text="État de l'objet avant modification"
    )
    
    donnees_apres = models.JSONField(
        _('Données après'),
        default=dict,
        blank=True,
        help_text="État de l'objet après modification"
    )
    
    date_action = models.DateTimeField(
        _('Date de l\'action'),
        auto_now_add=True,
        help_text="Date et heure de l'action"
    )
    
    class Meta:
        verbose_name = _('Log d\'audit')
        verbose_name_plural = _('Logs d\'audit')
        ordering = ['-date_action']
        indexes = [
            models.Index(fields=['utilisateur', 'date_action']),
            models.Index(fields=['action', 'date_action']),
            models.Index(fields=['content_type', 'object_id']),
        ]
    
    def __str__(self):
        """Représentation string du log."""
        user_str = self.utilisateur.username if self.utilisateur else "Système"
        return f"{user_str} - {self.action} - {self.date_action.strftime('%d/%m/%Y %H:%M')}"


class ContactMessage(models.Model):
    """
    Modèle pour les messages de contact des utilisateurs.
    
    Permet aux utilisateurs de contacter l'équipe support
    via un formulaire de contact.
    """
    
    STATUT_CHOICES = [
        ('NOUVEAU', _('Nouveau')),
        ('EN_COURS', _('En cours de traitement')),
        ('RESOLU', _('Résolu')),
        ('FERME', _('Fermé')),
    ]
    
    CATEGORIE_CHOICES = [
        ('SUPPORT', _('Support technique')),
        ('FACTURATION', _('Facturation')),
        ('SUGGESTION', _('Suggestion')),
        ('PLAINTE', _('Plainte')),
        ('AUTRE', _('Autre')),
    ]
    
    # Expéditeur
    utilisateur = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='contact_messages',
        verbose_name=_('Utilisateur'),
        help_text="Utilisateur expéditeur (si connecté)"
    )
    
    nom = models.CharField(
        _('Nom'),
        max_length=100,
        help_text="Nom de l'expéditeur"
    )
    
    email = models.EmailField(
        _('Email'),
        help_text="Email de l'expéditeur"
    )
    
    telephone = models.CharField(
        _('Téléphone'),
        max_length=15,
        blank=True,
        help_text="Numéro de téléphone (optionnel)"
    )
    
    # Message
    categorie = models.CharField(
        _('Catégorie'),
        max_length=20,
        choices=CATEGORIE_CHOICES,
        default='SUPPORT',
        help_text="Catégorie du message"
    )
    
    sujet = models.CharField(
        _('Sujet'),
        max_length=200,
        help_text="Sujet du message"
    )
    
    message = models.TextField(
        _('Message'),
        help_text="Contenu du message"
    )
    
    # Traitement
    statut = models.CharField(
        _('Statut'),
        max_length=20,
        choices=STATUT_CHOICES,
        default='NOUVEAU',
        help_text="Statut du message"
    )
    
    assigne_a = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_messages',
        verbose_name=_('Assigné à'),
        help_text="Membre de l'équipe assigné"
    )
    
    reponse = models.TextField(
        _('Réponse'),
        blank=True,
        help_text="Réponse de l'équipe"
    )
    
    # Métadonnées
    date_creation = models.DateTimeField(
        _('Date de création'),
        auto_now_add=True,
        help_text="Date de réception du message"
    )
    
    date_traitement = models.DateTimeField(
        _('Date de traitement'),
        null=True,
        blank=True,
        help_text="Date de première prise en charge"
    )
    
    date_resolution = models.DateTimeField(
        _('Date de résolution'),
        null=True,
        blank=True,
        help_text="Date de résolution du message"
    )
    
    adresse_ip = models.GenericIPAddressField(
        _('Adresse IP'),
        null=True,
        blank=True,
        help_text="Adresse IP de l'expéditeur"
    )
    
    class Meta:
        verbose_name = _('Message de contact')
        verbose_name_plural = _('Messages de contact')
        ordering = ['-date_creation']
    
    def __str__(self):
        """Représentation string du message."""
        return f"{self.nom} - {self.sujet} ({self.statut})"


class FAQ(models.Model):
    """
    Modèle pour les questions fréquemment posées.
    
    Permet de gérer une base de connaissances
    pour réduire les demandes de support.
    """
    
    CATEGORIE_CHOICES = [
        ('GENERAL', _('Général')),
        ('COMPTE', _('Compte utilisateur')),
        ('EVENEMENTS', _('Événements')),
        ('PAIEMENTS', _('Paiements')),
        ('ABONNEMENTS', _('Abonnements')),
        ('TECHNIQUE', _('Technique')),
    ]
    
    question = models.CharField(
        _('Question'),
        max_length=300,
        help_text="Question fréquemment posée"
    )
    
    reponse = models.TextField(
        _('Réponse'),
        help_text="Réponse détaillée à la question"
    )
    
    categorie = models.CharField(
        _('Catégorie'),
        max_length=20,
        choices=CATEGORIE_CHOICES,
        default='GENERAL',
        help_text="Catégorie de la question"
    )
    
    ordre = models.PositiveIntegerField(
        _('Ordre d\'affichage'),
        default=0,
        help_text="Ordre d'affichage dans la liste"
    )
    
    actif = models.BooleanField(
        _('Actif'),
        default=True,
        help_text="Question visible publiquement"
    )
    
    # Statistiques
    nombre_vues = models.PositiveIntegerField(
        _('Nombre de vues'),
        default=0,
        help_text="Nombre de fois que la question a été consultée"
    )
    
    utile_oui = models.PositiveIntegerField(
        _('Votes utiles'),
        default=0,
        help_text="Nombre de votes 'utile'"
    )
    
    utile_non = models.PositiveIntegerField(
        _('Votes non utiles'),
        default=0,
        help_text="Nombre de votes 'non utile'"
    )
    
    # Métadonnées
    date_creation = models.DateTimeField(
        _('Date de création'),
        auto_now_add=True,
        help_text="Date de création de la FAQ"
    )
    
    date_modification = models.DateTimeField(
        _('Date de modification'),
        auto_now=True,
        help_text="Date de dernière modification"
    )
    
    createur = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='faqs_created',
        verbose_name=_('Créateur'),
        help_text="Utilisateur qui a créé cette FAQ"
    )
    
    class Meta:
        verbose_name = _('Question fréquente')
        verbose_name_plural = _('Questions fréquentes')
        ordering = ['categorie', 'ordre', 'question']
    
    def __str__(self):
        """Représentation string de la FAQ."""
        return self.question
    
    def increment_views(self):
        """Incrémente le compteur de vues."""
        self.nombre_vues += 1
        self.save(update_fields=['nombre_vues'])
    
    def vote_useful(self, useful=True):
        """Enregistre un vote d'utilité."""
        if useful:
            self.utile_oui += 1
        else:
            self.utile_non += 1
        self.save(update_fields=['utile_oui', 'utile_non'])
    
    def get_usefulness_ratio(self):
        """Calcule le ratio d'utilité."""
        total_votes = self.utile_oui + self.utile_non
        if total_votes == 0:
            return 0
        return (self.utile_oui / total_votes) * 100


class SystemStatus(models.Model):
    """
    Modèle pour le statut du système et les maintenances.
    
    Permet d'informer les utilisateurs des maintenances
    et problèmes techniques.
    """
    
    STATUT_CHOICES = [
        ('OPERATIONNEL', _('Opérationnel')),
        ('DEGRADED', _('Performance dégradée')),
        ('MAINTENANCE', _('Maintenance programmée')),
        ('INCIDENT', _('Incident en cours')),
        ('HORS_LIGNE', _('Hors ligne')),
    ]
    
    SEVERITE_CHOICES = [
        ('INFO', _('Information')),
        ('ATTENTION', _('Attention')),
        ('CRITIQUE', _('Critique')),
    ]
    
    titre = models.CharField(
        _('Titre'),
        max_length=200,
        help_text="Titre du statut ou incident"
    )
    
    description = models.TextField(
        _('Description'),
        help_text="Description détaillée"
    )
    
    statut = models.CharField(
        _('Statut'),
        max_length=20,
        choices=STATUT_CHOICES,
        default='OPERATIONNEL',
        help_text="Statut actuel du système"
    )
    
    severite = models.CharField(
        _('Sévérité'),
        max_length=10,
        choices=SEVERITE_CHOICES,
        default='INFO',
        help_text="Niveau de sévérité"
    )
    
    # Dates
    date_debut = models.DateTimeField(
        _('Date de début'),
        help_text="Date de début de l'incident/maintenance"
    )
    
    date_fin_prevue = models.DateTimeField(
        _('Date de fin prévue'),
        null=True,
        blank=True,
        help_text="Date de fin prévue"
    )
    
    date_fin_reelle = models.DateTimeField(
        _('Date de fin réelle'),
        null=True,
        blank=True,
        help_text="Date de fin réelle"
    )
    
    # Configuration
    afficher_banniere = models.BooleanField(
        _('Afficher bannière'),
        default=True,
        help_text="Afficher une bannière d'information"
    )
    
    bloquer_acces = models.BooleanField(
        _('Bloquer accès'),
        default=False,
        help_text="Bloquer l'accès à l'application"
    )
    
    # Métadonnées
    date_creation = models.DateTimeField(
        _('Date de création'),
        auto_now_add=True,
        help_text="Date de création du statut"
    )
    
    date_modification = models.DateTimeField(
        _('Date de modification'),
        auto_now=True,
        help_text="Date de dernière modification"
    )
    
    createur = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='system_statuses',
        verbose_name=_('Créateur'),
        help_text="Utilisateur qui a créé ce statut"
    )
    
    class Meta:
        verbose_name = _('Statut système')
        verbose_name_plural = _('Statuts système')
        ordering = ['-date_creation']
    
    def __str__(self):
        """Représentation string du statut."""
        return f"{self.titre} - {self.statut}"
    
    def is_active(self):
        """Vérifie si le statut est actif."""
        from django.utils import timezone
        now = timezone.now()
        
        if self.date_fin_reelle:
            return now <= self.date_fin_reelle
        elif self.date_fin_prevue:
            return now <= self.date_fin_prevue
        else:
            return True  # Pas de date de fin définie

