"""
Configuration de l'interface d'administration pour les modèles core.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .models import AppSettings, AuditLog, ContactMessage, FAQ, SystemStatus


@admin.register(AppSettings)
class AppSettingsAdmin(admin.ModelAdmin):
    """Interface d'administration pour les paramètres d'application."""
    
    list_display = [
        'cle', 'valeur', 'type_valeur', 'categorie', 'modifiable'
    ]
    
    list_filter = ['type_valeur', 'categorie', 'modifiable']
    search_fields = ['cle', 'description']
    
    list_editable = ['valeur']
    
    fieldsets = [
        (_('Paramètre'), {
            'fields': ('cle', 'valeur', 'type_valeur')
        }),
        (_('Métadonnées'), {
            'fields': ('description', 'categorie', 'modifiable')
        }),
    ]
    
    def get_readonly_fields(self, request, obj=None):
        """Rend certains champs en lecture seule selon les permissions."""
        readonly = ['date_creation', 'date_modification']
        if obj and not obj.modifiable:
            readonly.extend(['cle', 'valeur', 'type_valeur'])
        return readonly


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Interface d'administration pour les logs d'audit."""
    
    list_display = [
        'utilisateur', 'action', 'description', 'date_action', 'adresse_ip'
    ]
    
    list_filter = ['action', 'date_action', 'content_type']
    search_fields = ['utilisateur__username', 'description', 'adresse_ip']
    
    readonly_fields = [
        'utilisateur', 'action', 'description', 'content_type',
        'object_id', 'adresse_ip', 'user_agent', 'donnees_avant',
        'donnees_apres', 'date_action'
    ]
    
    def has_add_permission(self, request):
        """Empêche l'ajout manuel de logs."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Empêche la modification des logs."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Empêche la suppression des logs."""
        return False


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    """Interface d'administration pour les messages de contact."""
    
    list_display = [
        'nom', 'email', 'sujet', 'categorie', 'statut',
        'date_creation', 'assigne_a'
    ]
    
    list_filter = ['categorie', 'statut', 'date_creation']
    search_fields = ['nom', 'email', 'sujet', 'message']
    
    list_editable = ['statut', 'assigne_a']
    
    readonly_fields = ['date_creation', 'adresse_ip']
    
    fieldsets = [
        (_('Expéditeur'), {
            'fields': ('utilisateur', 'nom', 'email', 'telephone')
        }),
        (_('Message'), {
            'fields': ('categorie', 'sujet', 'message')
        }),
        (_('Traitement'), {
            'fields': ('statut', 'assigne_a', 'reponse')
        }),
        (_('Métadonnées'), {
            'fields': ('date_creation', 'date_traitement', 'date_resolution', 'adresse_ip'),
            'classes': ('collapse',)
        }),
    ]
    
    actions = ['assign_to_me', 'mark_as_resolved']
    
    def assign_to_me(self, request, queryset):
        """Assigne les messages à l'utilisateur actuel."""
        updated = queryset.update(assigne_a=request.user)
        self.message_user(request, f'{updated} message(s) assigné(s) à vous.')
    assign_to_me.short_description = _('M\'assigner les messages')
    
    def mark_as_resolved(self, request, queryset):
        """Marque les messages comme résolus."""
        from django.utils import timezone
        updated = queryset.update(
            statut='RESOLU',
            date_resolution=timezone.now()
        )
        self.message_user(request, f'{updated} message(s) marqué(s) comme résolu(s).')
    mark_as_resolved.short_description = _('Marquer comme résolus')


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    """Interface d'administration pour les FAQ."""
    
    list_display = [
        'question', 'categorie', 'actif', 'ordre', 'nombre_vues',
        'get_usefulness_ratio'
    ]
    
    list_filter = ['categorie', 'actif']
    search_fields = ['question', 'reponse']
    
    list_editable = ['actif', 'ordre']
    
    readonly_fields = [
        'nombre_vues', 'utile_oui', 'utile_non', 'get_usefulness_ratio',
        'date_creation', 'date_modification'
    ]
    
    fieldsets = [
        (_('Question'), {
            'fields': ('question', 'reponse', 'categorie')
        }),
        (_('Configuration'), {
            'fields': ('actif', 'ordre')
        }),
        (_('Statistiques'), {
            'fields': (
                'nombre_vues', 'utile_oui', 'utile_non',
                'get_usefulness_ratio'
            ),
            'classes': ('collapse',)
        }),
        (_('Métadonnées'), {
            'fields': ('createur', 'date_creation', 'date_modification'),
            'classes': ('collapse',)
        }),
    ]
    
    def get_usefulness_ratio(self, obj):
        """Affiche le ratio d'utilité."""
        ratio = obj.get_usefulness_ratio()
        if ratio >= 80:
            color = 'green'
        elif ratio >= 60:
            color = 'orange'
        else:
            color = 'red'
        
        return format_html(
            '<span style="color: {};">{:.1f}%</span>',
            color, ratio
        )
    get_usefulness_ratio.short_description = _('Utilité')


@admin.register(SystemStatus)
class SystemStatusAdmin(admin.ModelAdmin):
    """Interface d'administration pour le statut système."""
    
    list_display = [
        'titre', 'statut', 'severite', 'date_debut',
        'date_fin_prevue', 'afficher_banniere', 'bloquer_acces'
    ]
    
    list_filter = ['statut', 'severite', 'afficher_banniere', 'bloquer_acces']
    search_fields = ['titre', 'description']
    
    list_editable = ['afficher_banniere', 'bloquer_acces']
    
    readonly_fields = ['date_creation', 'date_modification']
    
    fieldsets = [
        (_('Statut'), {
            'fields': ('titre', 'description', 'statut', 'severite')
        }),
        (_('Période'), {
            'fields': ('date_debut', 'date_fin_prevue', 'date_fin_reelle')
        }),
        (_('Configuration'), {
            'fields': ('afficher_banniere', 'bloquer_acces')
        }),
        (_('Métadonnées'), {
            'fields': ('createur', 'date_creation', 'date_modification'),
            'classes': ('collapse',)
        }),
    ]

