"""
Configuration de l'interface d'administration pour les utilisateurs.

Ce module configure l'affichage et les fonctionnalités de l'interface
d'administration Django pour les modèles liés aux utilisateurs.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from .models import User, UserVerification, Follow


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Interface d'administration pour le modèle User personnalisé.
    
    Affiche et permet de gérer tous les aspects des comptes utilisateurs
    avec des fonctionnalités étendues pour la modération.
    """
    
    # Champs affichés dans la liste
    list_display = [
        'username', 'email', 'get_full_name', 'telephone', 
        'est_verifie', 'is_active', 'is_staff', 'date_creation',
        'get_events_count', 'get_followers_count'
    ]
    
    # Champs de recherche
    search_fields = ['username', 'email', 'first_name', 'last_name', 'telephone']
    
    # Filtres latéraux
    list_filter = [
        'est_verifie', 'is_active', 'is_staff', 'is_superuser',
        'date_creation', 'date_verification', 'notifications_email',
        'notifications_push'
    ]
    
    # Champs modifiables directement dans la liste
    list_editable = ['is_active', 'est_verifie']
    
    # Nombre d'éléments par page
    list_per_page = 25
    
    # Champs en lecture seule
    readonly_fields = [
        'date_creation', 'date_modification', 'date_verification',
        'derniere_connexion_ip', 'last_login', 'date_joined'
    ]
    
    # Organisation des champs dans le formulaire
    fieldsets = BaseUserAdmin.fieldsets + (
        (_('Informations personnelles étendues'), {
            'fields': ('telephone', 'date_naissance', 'photo_profil', 'bio')
        }),
        (_('Vérification'), {
            'fields': ('est_verifie', 'date_verification')
        }),
        (_('Préférences'), {
            'fields': ('notifications_email', 'notifications_push')
        }),
        (_('Métadonnées'), {
            'fields': ('date_creation', 'date_modification', 'derniere_connexion_ip'),
            'classes': ('collapse',)
        }),
    )
    
    # Champs pour la création d'utilisateur
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (_('Informations supplémentaires'), {
            'fields': ('email', 'telephone', 'first_name', 'last_name')
        }),
    )
    
    # Actions personnalisées
    actions = ['verify_users', 'unverify_users', 'activate_users', 'deactivate_users']
    
    def get_full_name(self, obj):
        """Affiche le nom complet de l'utilisateur."""
        return obj.get_full_name() or '-'
    get_full_name.short_description = _('Nom complet')
    
    def get_events_count(self, obj):
        """Affiche le nombre d'événements créés."""
        count = obj.get_events_count()
        if count > 0:
            url = reverse('admin:events_event_changelist') + f'?createur__id__exact={obj.id}'
            return format_html('<a href="{}">{} événements</a>', url, count)
        return '0 événement'
    get_events_count.short_description = _('Événements')
    
    def get_followers_count(self, obj):
        """Affiche le nombre de followers."""
        return obj.get_followers_count()
    get_followers_count.short_description = _('Followers')
    
    def verify_users(self, request, queryset):
        """Action pour vérifier des utilisateurs."""
        updated = queryset.update(
            est_verifie=True,
            date_verification=timezone.now()
        )
        self.message_user(
            request,
            f'{updated} utilisateur(s) vérifié(s) avec succès.'
        )
    verify_users.short_description = _('Vérifier les utilisateurs sélectionnés')
    
    def unverify_users(self, request, queryset):
        """Action pour dé-vérifier des utilisateurs."""
        updated = queryset.update(
            est_verifie=False,
            date_verification=None
        )
        self.message_user(
            request,
            f'{updated} utilisateur(s) dé-vérifié(s) avec succès.'
        )
    unverify_users.short_description = _('Dé-vérifier les utilisateurs sélectionnés')
    
    def activate_users(self, request, queryset):
        """Action pour activer des utilisateurs."""
        updated = queryset.update(is_active=True)
        self.message_user(
            request,
            f'{updated} utilisateur(s) activé(s) avec succès.'
        )
    activate_users.short_description = _('Activer les utilisateurs sélectionnés')
    
    def deactivate_users(self, request, queryset):
        """Action pour désactiver des utilisateurs."""
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            f'{updated} utilisateur(s) désactivé(s) avec succès.'
        )
    deactivate_users.short_description = _('Désactiver les utilisateurs sélectionnés')


@admin.register(UserVerification)
class UserVerificationAdmin(admin.ModelAdmin):
    """
    Interface d'administration pour les vérifications d'utilisateurs.
    """
    
    list_display = [
        'utilisateur', 'statut', 'date_soumission', 'date_validation',
        'validateur', 'get_document_link'
    ]
    
    search_fields = ['utilisateur__username', 'utilisateur__email']
    list_filter = ['statut', 'date_soumission', 'date_validation']
    list_editable = ['statut']
    
    # Remove utilisateur from readonly_fields
    readonly_fields = ['date_soumission']
    
    # Add utilisateur to required fields
    required_fields = ['utilisateur']
    
    fieldsets = [
        (_('Utilisateur'), {
            'fields': ('utilisateur', 'date_soumission'),
            'classes': ('wide',)  # Make this section more visible
        }),
        (_('Documents'), {
            'fields': ('document_identite', 'document_selfie')
        }),
        (_('Validation'), {
            'fields': ('statut', 'validateur', 'date_validation', 'commentaire_admin')
        }),
    ]
    
    # Actions personnalisées
    actions = ['approve_verifications', 'reject_verifications']
    
    def get_document_link(self, obj):
        """Affiche un lien vers le document d'identité."""
        if obj.document_identite:
            return format_html(
                '<a href="{}" target="_blank">Voir le document</a>',
                obj.document_identite.url
            )
        return '-'
    get_document_link.short_description = _('Document')
    
    def approve_verifications(self, request, queryset):
        """Action pour approuver des vérifications."""
        updated = 0
        for verification in queryset.filter(statut='EN_ATTENTE'):
            verification.statut = 'APPROUVE'
            verification.validateur = request.user
            verification.date_validation = timezone.now()
            verification.save()
            
            # Mettre à jour l'utilisateur
            verification.utilisateur.est_verifie = True
            verification.utilisateur.date_verification = timezone.now()
            verification.utilisateur.save()
            
            updated += 1
        
        self.message_user(
            request,
            f'{updated} vérification(s) approuvée(s) avec succès.'
        )
    approve_verifications.short_description = _('Approuver les vérifications sélectionnées')
    
    def reject_verifications(self, request, queryset):
        """Action pour rejeter des vérifications."""
        updated = 0
        for verification in queryset.filter(statut='EN_ATTENTE'):
            verification.statut = 'REJETE'
            verification.validateur = request.user
            verification.date_validation = timezone.now()
            verification.save()
            updated += 1
        
        self.message_user(
            request,
            f'{updated} vérification(s) rejetée(s) avec succès.'
        )
    reject_verifications.short_description = _('Rejeter les vérifications sélectionnées')
    
    def save_model(self, request, obj, form, change):
        """Sauvegarde personnalisée pour enregistrer le validateur."""
        if change and 'statut' in form.changed_data:
            if obj.statut in ['APPROUVE', 'REJETE']:
                obj.validateur = request.user
                obj.date_validation = timezone.now()
                
                # Si approuvé, mettre à jour l'utilisateur
                if obj.statut == 'APPROUVE':
                    obj.utilisateur.est_verifie = True
                    obj.utilisateur.date_verification = timezone.now()
                    obj.utilisateur.save()
        
        super().save_model(request, obj, form, change)


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    """
    Interface d'administration pour les relations de suivi.
    
    Permet de visualiser et gérer les relations de suivi
    entre les utilisateurs.
    """
    
    # Champs affichés dans la liste
    list_display = [
        'follower', 'following', 'date_suivi', 'notifications_activees'
    ]
    
    # Champs de recherche
    search_fields = [
        'follower__username', 'follower__email',
        'following__username', 'following__email'
    ]
    
    # Filtres latéraux
    list_filter = ['notifications_activees', 'date_suivi']
    
    # Champs modifiables directement dans la liste
    list_editable = ['notifications_activees']
    
    # Champs en lecture seule
    readonly_fields = ['date_suivi']
    
    # Nombre d'éléments par page
    list_per_page = 50
    
    def get_queryset(self, request):
        """Optimise les requêtes avec select_related."""
        return super().get_queryset(request).select_related('follower', 'following')

