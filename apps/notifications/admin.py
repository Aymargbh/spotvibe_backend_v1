"""
Configuration de l'interface d'administration pour les notifications.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .models import (
    NotificationTemplate, Notification, NotificationPreference,
    PushToken, NotificationBatch
)


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    """Interface d'administration pour les templates de notification."""
    
    list_display = [
        'nom', 'type_notification', 'actif', 'get_canaux_actifs',
        'date_modification'
    ]
    
    list_filter = ['type_notification', 'actif', 'date_creation']
    search_fields = ['nom', 'description', 'type_notification']
    
    fieldsets = [
        (_('Informations de base'), {
            'fields': ('type_notification', 'nom', 'description', 'actif')
        }),
        (_('Contenu Email'), {
            'fields': ('titre_email', 'contenu_email'),
            'classes': ('collapse',)
        }),
        (_('Contenu Push'), {
            'fields': ('titre_push', 'contenu_push'),
            'classes': ('collapse',)
        }),
        (_('Contenu SMS'), {
            'fields': ('contenu_sms',),
            'classes': ('collapse',)
        }),
        (_('Contenu In-App'), {
            'fields': ('contenu_in_app',),
            'classes': ('collapse',)
        }),
        (_('Configuration'), {
            'fields': ('canaux_actifs', 'variables_disponibles'),
            'classes': ('collapse',)
        }),
    ]
    
    def get_canaux_actifs(self, obj):
        """Affiche les canaux actifs."""
        if obj.canaux_actifs:
            return ', '.join(obj.canaux_actifs)
        return '-'
    get_canaux_actifs.short_description = _('Canaux actifs')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Interface d'administration pour les notifications."""
    
    list_display = [
        'utilisateur', 'titre', 'type_notification', 'priorite',
        'statut', 'date_creation', 'is_read'
    ]
    
    list_filter = [
        'type_notification', 'priorite', 'statut',
        'date_creation', 'date_lecture'
    ]
    
    search_fields = ['utilisateur__username', 'titre', 'message']
    
    readonly_fields = [
        'date_creation', 'date_envoi', 'date_lecture', 'is_read'
    ]
    
    fieldsets = [
        (_('Destinataire'), {
            'fields': ('utilisateur',)
        }),
        (_('Contenu'), {
            'fields': ('type_notification', 'titre', 'message', 'priorite')
        }),
        (_('Objet concerné'), {
            'fields': ('content_type', 'object_id'),
            'classes': ('collapse',)
        }),
        (_('Statut'), {
            'fields': ('statut', 'date_creation', 'date_envoi', 'date_lecture')
        }),
        (_('Action'), {
            'fields': ('lien_action', 'donnees_supplementaires'),
            'classes': ('collapse',)
        }),
    ]
    
    actions = ['mark_as_read', 'mark_as_sent']
    
    def is_read(self, obj):
        """Affiche si la notification a été lue."""
        if obj.is_read():
            return format_html('<span style="color: green;">✓ Lu</span>')
        return format_html('<span style="color: red;">✗ Non lu</span>')
    is_read.short_description = _('Lu')
    
    def mark_as_read(self, request, queryset):
        """Marque les notifications comme lues."""
        updated = 0
        for notification in queryset:
            if not notification.is_read():
                notification.mark_as_read()
                updated += 1
        
        self.message_user(request, f'{updated} notification(s) marquée(s) comme lue(s).')
    mark_as_read.short_description = _('Marquer comme lues')
    
    def mark_as_sent(self, request, queryset):
        """Marque les notifications comme envoyées."""
        from django.utils import timezone
        updated = queryset.filter(statut='EN_ATTENTE').update(
            statut='ENVOYE',
            date_envoi=timezone.now()
        )
        self.message_user(request, f'{updated} notification(s) marquée(s) comme envoyée(s).')
    mark_as_sent.short_description = _('Marquer comme envoyées')


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    """Interface d'administration pour les préférences de notification."""
    
    list_display = [
        'utilisateur', 'type_notification', 'canal', 'actif', 'frequence'
    ]
    
    list_filter = ['type_notification', 'canal', 'actif', 'frequence']
    search_fields = ['utilisateur__username']
    
    list_editable = ['actif']


@admin.register(PushToken)
class PushTokenAdmin(admin.ModelAdmin):
    """Interface d'administration pour les tokens push."""
    
    list_display = [
        'utilisateur', 'plateforme', 'nom_appareil', 'actif',
        'derniere_utilisation', 'get_delivery_rate'
    ]
    
    list_filter = ['plateforme', 'actif', 'derniere_utilisation']
    search_fields = ['utilisateur__username', 'nom_appareil', 'token']
    
    readonly_fields = [
        'token', 'derniere_utilisation', 'notifications_envoyees',
        'notifications_livrees', 'get_delivery_rate'
    ]
    
    def get_delivery_rate(self, obj):
        """Affiche le taux de livraison."""
        rate = obj.get_delivery_rate()
        if rate >= 90:
            color = 'green'
        elif rate >= 70:
            color = 'orange'
        else:
            color = 'red'
        
        return format_html(
            '<span style="color: {};">{:.1f}%</span>',
            color, rate
        )
    get_delivery_rate.short_description = _('Taux de livraison')


@admin.register(NotificationBatch)
class NotificationBatchAdmin(admin.ModelAdmin):
    """Interface d'administration pour les campagnes de notification."""
    
    list_display = [
        'nom', 'template', 'statut',
        'get_nombre_destinataires', 'date_planification', 'get_delivery_rate', 'get_read_rate'
    ]
    
    list_filter = ['statut', 'date_planification', 'date_debut_envoi']
    search_fields = ['nom', 'description']
    
    readonly_fields = [
        'date_debut_envoi', 'date_fin_envoi',
        'get_nombre_destinataires', 'get_nombre_envoyes', 'get_nombre_livres',
        'get_nombre_lus', 'get_delivery_rate', 'get_read_rate'
    ]
    
    fieldsets = [
        (_('Informations de base'), {
            'fields': ('nom', 'description', 'template', 'createur')
        }),
        (_('Ciblage'), {
            'fields': ('destinataires', 'criteres_ciblage'),
            'classes': ('collapse',)
        }),
        (_("Planification"), {
            "fields": ("date_planification", "statut")
        }),
        (_('Résultats'), {
            'fields': (
                'get_nombre_destinataires', 'get_nombre_envoyes', 'get_nombre_livres',
                'get_nombre_lus', 'get_delivery_rate', 'get_read_rate'
            ),
            'classes': ('collapse',)
        }),
        (_('Dates d\'exécution'), {
            'fields': ('date_debut_envoi', 'date_fin_envoi'),
            'classes': ('collapse',)
        }),
    ]
    
    def get_delivery_rate(self, obj):
        """Affiche le taux de livraison."""
        rate = obj.get_delivery_rate()
        return format_html('{:.1f}%', rate)
    get_delivery_rate.short_description = _('Taux de livraison')
    
    def get_read_rate(self, obj):
        """Affiche le taux de lecture."""
        rate = obj.get_read_rate()
        return format_html("{:.1f}%", rate)
    get_read_rate.short_description = _("Taux de lecture")

    def get_nombre_destinataires(self, obj):
        return obj.nombre_destinataires
    get_nombre_destinataires.short_description = _("Destinataires")

    def get_nombre_envoyes(self, obj):
        return obj.nombre_envoyes
    get_nombre_envoyes.short_description = _("Envoyés")

    def get_nombre_livres(self, obj):
        return obj.nombre_livres
    get_nombre_livres.short_description = _("Livrés")

    def get_nombre_lus(self, obj):
        return obj.nombre_lus
    get_nombre_lus.short_description = _("Lus")