"""
Configuration de l'interface d'administration pour les abonnements.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.db.models import Count, Sum
from .models import SubscriptionPlan, Subscription, SubscriptionFeature, SubscriptionHistory


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    """Interface d'administration pour les plans d'abonnement."""
    
    list_display = [
        'nom', 'type_plan', 'prix', 'duree', 'actif', 'ordre', 'get_subscribers_count'
    ]
    list_editable = ['actif', 'ordre']
    list_filter = ['type_plan', 'duree', 'actif']
    search_fields = ['nom', 'description']
    ordering = ['ordre', 'prix']
    
    fieldsets = [
        (_('Informations de base'), {
            'fields': ('nom', 'type_plan', 'prix', 'duree', 'description')
        }),
        (_('Limites et avantages'), {
            'fields': (
                'max_evenements_par_mois', 'commission_reduite',
                'support_prioritaire', 'analytics_avances',
                'promotion_evenements', 'personnalisation_profil'
            )
        }),
        (_('Configuration'), {
            'fields': ('actif', 'ordre')
        }),
    ]
    
    def get_subscribers_count(self, obj):
        """Affiche le nombre d'abonnés actifs."""
        count = obj.get_subscribers_count()
        return format_html('<strong>{}</strong> abonnés', count)
    get_subscribers_count.short_description = _('Abonnés actifs')


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Interface d'administration pour les abonnements."""
    
    list_display = [
        'utilisateur', 'plan', 'statut', 'date_debut', 'date_fin',
        'prix_paye', 'renouvellement_automatique', 'days_remaining'
    ]
    
    list_filter = [
        'statut', 'plan__type_plan', 'renouvellement_automatique',
        'date_debut', 'date_fin'
    ]
    
    search_fields = ['utilisateur__username', 'utilisateur__email', 'plan__nom']
    
    readonly_fields = [
        'date_creation', 'date_modification', 'evenements_crees_ce_mois',
        'derniere_reinitialisation_compteur', 'days_remaining'
    ]
    
    fieldsets = [
        (_('Abonnement'), {
            'fields': ('utilisateur', 'plan', 'statut')
        }),
        (_('Période'), {
            'fields': ('date_debut', 'date_fin', 'days_remaining')
        }),
        (_('Paiement'), {
            'fields': ('prix_paye', 'reference_paiement')
        }),
        (_('Configuration'), {
            'fields': ('renouvellement_automatique',)
        }),
        (_('Utilisation'), {
            'fields': (
                'evenements_crees_ce_mois',
                'derniere_reinitialisation_compteur'
            ),
            'classes': ('collapse',)
        }),
        (_('Métadonnées'), {
            'fields': ('date_creation', 'date_modification'),
            'classes': ('collapse',)
        }),
    ]
    
    actions = ['activate_subscriptions', 'cancel_subscriptions']
    
    def days_remaining(self, obj):
        """Affiche les jours restants."""
        days = obj.days_remaining()
        if days > 0:
            return format_html('<span style="color: green;">{} jours</span>', days)
        return format_html('<span style="color: red;">Expiré</span>')
    days_remaining.short_description = _('Jours restants')
    
    def activate_subscriptions(self, request, queryset):
        """Active les abonnements sélectionnés."""
        updated = queryset.update(statut='ACTIF')
        self.message_user(request, f'{updated} abonnement(s) activé(s).')
    activate_subscriptions.short_description = _('Activer les abonnements')
    
    def cancel_subscriptions(self, request, queryset):
        """Annule les abonnements sélectionnés."""
        updated = queryset.update(statut='ANNULE')
        self.message_user(request, f'{updated} abonnement(s) annulé(s).')
    cancel_subscriptions.short_description = _('Annuler les abonnements')


@admin.register(SubscriptionFeature)
class SubscriptionFeatureAdmin(admin.ModelAdmin):
    """Interface d'administration pour les fonctionnalités d'abonnement."""
    
    list_display = ['plan', 'nom', 'inclus', 'limite', 'ordre']
    list_editable = ['inclus', 'ordre']
    list_filter = ['plan', 'inclus']
    search_fields = ['nom', 'description']
    ordering = ['plan', 'ordre']


@admin.register(SubscriptionHistory)
class SubscriptionHistoryAdmin(admin.ModelAdmin):
    """Interface d'administration pour l'historique des abonnements."""
    
    list_display = [
        'subscription', 'action', 'ancien_statut', 'nouveau_statut',
        'date_action', 'utilisateur_action'
    ]
    
    list_filter = ['action', 'date_action']
    search_fields = [
        'subscription__utilisateur__username',
        'subscription__plan__nom'
    ]
    
    readonly_fields = ['date_action']
    
    def get_queryset(self, request):
        """Optimise les requêtes."""
        return super().get_queryset(request).select_related(
            'subscription__utilisateur', 'subscription__plan', 'utilisateur_action'
        )

