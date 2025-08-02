"""
Configuration de l'interface d'administration pour l'authentification.
"""

from datetime import timedelta
from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .models import (
    SocialAccount, LoginAttempt, PasswordReset,
    EmailVerification, TwoFactorAuth
)


@admin.register(SocialAccount)
class SocialAccountAdmin(admin.ModelAdmin):
    """Interface d'administration pour les comptes sociaux."""
    
    list_display = [
        'utilisateur', 'provider', 'email', 'actif',
        'derniere_utilisation', 'is_token_valid'
    ]
    
    list_filter = ['provider', 'actif', 'date_creation']
    search_fields = ['utilisateur__username', 'email', 'social_id']
    
    readonly_fields = [
        'social_id', 'date_creation', 'date_modification',
        'derniere_utilisation', 'is_token_valid'
    ]
    
    fieldsets = [
        (_('Compte'), {
            'fields': ('utilisateur', 'provider', 'social_id', 'email', 'nom_complet')
        }),
        (_('Photo'), {
            'fields': ('photo_url',)
        }),
        (_('Tokens'), {
            'fields': ('access_token', 'refresh_token', 'token_expires_at'),
            'classes': ('collapse',)
        }),
        (_('Statut'), {
            'fields': ('actif', 'derniere_utilisation', 'is_token_valid')
        }),
        (_('Métadonnées'), {
            'fields': ('date_creation', 'date_modification'),
            'classes': ('collapse',)
        }),
    ]
    
    def is_token_valid(self, obj):
        """Affiche si le token est valide."""
        if obj.is_token_valid():
            return format_html('<span style="color: green;">✓ Valide</span>')
        return format_html('<span style="color: red;">✗ Expiré</span>')
    is_token_valid.short_description = _('Token valide')


@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    """Interface d'administration pour les tentatives de connexion."""
    
    list_display = [
        'email_tente', 'utilisateur', 'statut', 'adresse_ip',
        'date_tentative', 'pays', 'ville'
    ]
    
    list_filter = ['statut', 'date_tentative', 'pays']
    search_fields = ['email_tente', 'adresse_ip', 'utilisateur__username']
    
    readonly_fields = [
        'email_tente', 'utilisateur', 'statut', 'raison_echec',
        'adresse_ip', 'user_agent', 'pays', 'ville',
        'date_tentative', 'duree_session'
    ]
    
    def has_add_permission(self, request):
        """Empêche l'ajout manuel."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Empêche la modification."""
        return False


@admin.register(PasswordReset)
class PasswordResetAdmin(admin.ModelAdmin):
    """Interface d'administration pour les réinitialisations de mot de passe."""
    
    list_display = [
        'utilisateur', 'statut', 'date_creation', 'date_expiration',
        'is_valid', 'adresse_ip_creation'
    ]
    
    list_filter = ['statut', 'date_creation']
    search_fields = ['utilisateur__username', 'token']
    
    readonly_fields = [
        'token', 'date_creation', 'date_expiration', 'date_utilisation',
        'adresse_ip_creation', 'adresse_ip_utilisation', 'is_valid'
    ]
    
    def is_valid(self, obj):
        """Affiche si le token est valide."""
        if obj.is_valid():
            return format_html('<span style="color: green;">✓ Valide</span>')
        return format_html('<span style="color: red;">✗ Invalide</span>')
    is_valid.short_description = _('Valide')


@admin.register(EmailVerification)
class EmailVerificationAdmin(admin.ModelAdmin):
    """Interface d'administration pour les vérifications d'email."""
    
    list_display = [
        'utilisateur', 'email', 'type_verification', 'statut',
        'tentatives', 'date_creation', 'get_is_valid'  # Changed is_valid to get_is_valid
    ]
    
    list_filter = ['type_verification', 'statut', 'date_creation']
    search_fields = ['utilisateur__username', 'email', 'code']
    
    # Removed is_valid from readonly_fields
    readonly_fields = [
        'code', 'tentatives', 'date_creation', 'date_expiration',
        'date_verification', 'adresse_ip'
    ]
    
    fieldsets = [
        (_('Vérification'), {
            'fields': ('utilisateur', 'email', 'type_verification', 'code')
        }),
        (_('Statut'), {
            'fields': ('statut', 'tentatives', 'max_tentatives')
        }),
        (_('Dates'), {
            'fields': ('date_creation', 'date_expiration', 'date_verification'),
            'classes': ('collapse',)
        }),
        (_('Sécurité'), {
            'fields': ('adresse_ip',),
            'classes': ('collapse',)
        }),
    ]
    
    def get_is_valid(self, obj):
        """Affiche si le code est valide."""
        if obj and obj.date_expiration:  # Add null check
            if obj.is_valid():
                return format_html('<span style="color: green;">✓ Valide</span>')
        return format_html('<span style="color: red;">✗ Invalide</span>')
    get_is_valid.short_description = _('Validité')
    
    def save_model(self, request, obj, form, change):
        """Définit la date d'expiration si elle n'existe pas."""
        if not obj.date_expiration:
            obj.date_expiration = timezone.now() + timedelta(hours=24)
        super().save_model(request, obj, form, change)

@admin.register(TwoFactorAuth)
class TwoFactorAuthAdmin(admin.ModelAdmin):
    """Interface d'administration pour l'authentification 2FA."""
    
    list_display = [
        'utilisateur', 'actif', 'methode', 'derniere_utilisation',
        'date_activation', 'get_recovery_codes_count'
    ]
    
    list_filter = ['actif', 'methode', 'date_activation']
    search_fields = ['utilisateur__username']
    
    readonly_fields = [
        'secret_key', 'derniere_utilisation', 'date_activation',
        'get_recovery_codes_count'
    ]
    
    fieldsets = [
        (_('Configuration'), {
            'fields': ('utilisateur', 'actif', 'methode')
        }),
        (_('TOTP'), {
            'fields': ('secret_key',),
            'classes': ('collapse',)
        }),
        (_('Codes de récupération'), {
            'fields': ('codes_recuperation', 'get_recovery_codes_count'),
            'classes': ('collapse',)
        }),
        (_('Statistiques'), {
            'fields': ('derniere_utilisation', 'date_activation'),
            'classes': ('collapse',)
        }),
    ]
    
    def get_recovery_codes_count(self, obj):
        """Affiche le nombre de codes de récupération restants."""
        count = len(obj.codes_recuperation)
        if count > 5:
            color = 'green'
        elif count > 2:
            color = 'orange'
        else:
            color = 'red'
        
        return format_html(
            '<span style="color: {};">{} codes</span>',
            color, count
        )
    get_recovery_codes_count.short_description = _('Codes de récupération')

