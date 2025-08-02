"""
Configuration de l'interface d'administration pour le dashboard admin.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .models import AdminAction, DashboardWidget, AdminNotification


@admin.register(AdminAction)
class AdminActionAdmin(admin.ModelAdmin):
    """Interface d'administration pour les actions administrateur."""
    
    list_display = [
        'admin', 'action', 'description', 'date_action', 'adresse_ip'
    ]
    
    list_filter = ['action', 'date_action']
    search_fields = ['admin__username', 'description', 'adresse_ip']
    
    readonly_fields = [
        'admin', 'action', 'description', 'content_type', 'object_id',
        'date_action', 'adresse_ip', 'donnees_supplementaires'
    ]
    
    def has_add_permission(self, request):
        """Empêche l'ajout manuel."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Empêche la modification."""
        return False


@admin.register(DashboardWidget)
class DashboardWidgetAdmin(admin.ModelAdmin):
    """Interface d'administration pour les widgets de dashboard."""
    
    list_display = [
        'nom', 'type_widget', 'largeur', 'hauteur', 'ordre',
        'actif', 'createur'
    ]
    
    list_filter = ['type_widget', 'actif', 'date_creation']
    search_fields = ['nom', 'titre', 'description']
    
    list_editable = ['ordre', 'actif']
    
    fieldsets = [
        (_('Widget'), {
            'fields': ('nom', 'type_widget', 'titre', 'description')
        }),
        (_('Configuration'), {
            'fields': ('configuration', 'requete_sql'),
            'classes': ('collapse',)
        }),
        (_('Affichage'), {
            'fields': ('largeur', 'hauteur', 'ordre', 'actif')
        }),
        (_('Permissions'), {
            'fields': ('visible_pour',),
            'classes': ('collapse',)
        }),
        (_('Métadonnées'), {
            'fields': ('createur', 'date_creation', 'date_modification'),
            'classes': ('collapse',)
        }),
    ]


@admin.register(AdminNotification)
class AdminNotificationAdmin(admin.ModelAdmin):
    """Interface d'administration pour les notifications admin."""
    
    list_display = [
        'titre', 'type_notification', 'priorite', 'statut',
        'date_creation', 'date_resolution'
    ]
    
    list_filter = ['type_notification', 'priorite', 'statut', 'date_creation']
    search_fields = ['titre', 'message']
    
    list_editable = ['statut']
    
    readonly_fields = ['date_creation', 'date_resolution']
    
    fieldsets = [
        (_('Notification'), {
            'fields': ('type_notification', 'titre', 'message', 'priorite')
        }),
        (_('Statut'), {
            'fields': ('statut', 'date_creation', 'date_resolution')
        }),
        (_('Destinataires'), {
            'fields': ('destinataires',)
        }),
        (_('Objet concerné'), {
            'fields': ('content_type', 'object_id'),
            'classes': ('collapse',)
        }),
        (_('Action'), {
            'fields': ('lien_action', 'donnees_supplementaires'),
            'classes': ('collapse',)
        }),
    ]
    
    actions = ['mark_as_resolved']
    
    def mark_as_resolved(self, request, queryset):
        """Marque les notifications comme résolues."""
        updated = 0
        for notification in queryset.filter(statut__in=['NOUVEAU', 'VU', 'EN_COURS']):
            notification.mark_as_resolved(request.user)
            updated += 1
        
        self.message_user(request, f'{updated} notification(s) marquée(s) comme résolue(s).')
    mark_as_resolved.short_description = _('Marquer comme résolues')

