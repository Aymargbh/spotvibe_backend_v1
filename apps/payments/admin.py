"""
Configuration de l'interface d'administration pour les paiements.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.db.models import Sum
from .models import Payment, MomoTransaction, Commission, Refund


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Interface d'administration pour les paiements."""
    
    list_display = [
        'uuid', 'utilisateur', 'type_paiement', 'montant', 'statut',
        'methode_paiement', 'date_creation', 'get_net_amount'
    ]
    
    list_filter = [
        'type_paiement', 'statut', 'methode_paiement',
        'date_creation', 'date_traitement'
    ]
    
    search_fields = [
        'uuid', 'utilisateur__username', 'reference_externe',
        'reference_interne'
    ]
    
    readonly_fields = [
        'uuid', 'montant_net', 'date_creation', 'date_traitement',
        'get_commission_amount'
    ]
    
    fieldsets = [
        (_('Informations de base'), {
            'fields': ('uuid', 'utilisateur', 'type_paiement')
        }),
        (_('Montants'), {
            'fields': ('montant', 'frais', 'montant_net', 'get_commission_amount')
        }),
        (_('Statut et méthode'), {
            'fields': ('statut', 'methode_paiement')
        }),
        (_('Références'), {
            'fields': ('reference_externe', 'reference_interne')
        }),
        (_('Relations'), {
            'fields': ('subscription', 'event_ticket'),
            'classes': ('collapse',)
        }),
        (_('Dates'), {
            'fields': ('date_creation', 'date_traitement', 'date_expiration'),
            'classes': ('collapse',)
        }),
        (_('Informations supplémentaires'), {
            'fields': ('description', 'telephone_paiement', 'donnees_reponse'),
            'classes': ('collapse',)
        }),
    ]
    
    actions = ['mark_as_successful', 'mark_as_failed']
    
    def get_net_amount(self, obj):
        """Affiche le montant net."""
        return format_html('{:,.0f} FCFA', obj.montant_net)
    get_net_amount.short_description = _('Montant net')
    
    def get_commission_amount(self, obj):
        """Affiche le montant de commission."""
        commission = obj.get_commission_amount()
        if commission > 0:
            return format_html('{:,.0f} FCFA', commission)
        return '0 FCFA'
    get_commission_amount.short_description = _('Commission')
    
    def mark_as_successful(self, request, queryset):
        """Marque les paiements comme réussis."""
        updated = queryset.filter(statut='EN_COURS').update(statut='REUSSI')
        self.message_user(request, f'{updated} paiement(s) marqué(s) comme réussi(s).')
    mark_as_successful.short_description = _('Marquer comme réussis')
    
    def mark_as_failed(self, request, queryset):
        """Marque les paiements comme échoués."""
        updated = queryset.filter(statut='EN_COURS').update(statut='ECHEC')
        self.message_user(request, f'{updated} paiement(s) marqué(s) comme échoué(s).')
    mark_as_failed.short_description = _('Marquer comme échoués')


@admin.register(MomoTransaction)
class MomoTransactionAdmin(admin.ModelAdmin):
    """Interface d'administration pour les transactions Mobile Money."""
    
    list_display = [
        'transaction_id', 'payment', 'operateur', 'numero_telephone',
        'type_transaction', 'date_initiation', 'is_confirmed'
    ]
    
    list_filter = [
        'operateur', 'type_transaction', 'webhook_recu',
        'date_initiation', 'date_confirmation'
    ]
    
    search_fields = [
        'transaction_id', 'reference_operateur', 'numero_telephone',
        'payment__uuid'
    ]
    
    readonly_fields = [
        'date_initiation', 'date_confirmation', 'webhook_recu',
        'donnees_webhook'
    ]
    
    def is_confirmed(self, obj):
        """Affiche si la transaction est confirmée."""
        if obj.is_confirmed():
            return format_html('<span style="color: green;">✓ Confirmé</span>')
        return format_html('<span style="color: red;">✗ Non confirmé</span>')
    is_confirmed.short_description = _('Confirmé')


@admin.register(Commission)
class CommissionAdmin(admin.ModelAdmin):
    """Interface d'administration pour les commissions."""
    
    list_display = [
        'payment', 'type_commission', 'organisateur', 'montant_base',
        'taux_commission', 'montant_commission', 'statut', 'date_calcul'
    ]
    
    list_filter = [
        'type_commission', 'statut', 'date_calcul', 'date_paiement'
    ]
    
    search_fields = [
        'payment__uuid', 'organisateur__username', 'event__titre'
    ]
    
    readonly_fields = ['montant_commission', 'date_calcul']
    
    actions = ['mark_as_paid']
    
    def mark_as_paid(self, request, queryset):
        """Marque les commissions comme payées."""
        from django.utils import timezone
        updated = queryset.filter(statut='CALCULEE').update(
            statut='PAYEE',
            date_paiement=timezone.now()
        )
        self.message_user(request, f'{updated} commission(s) marquée(s) comme payée(s).')
    mark_as_paid.short_description = _('Marquer comme payées')


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    """Interface d'administration pour les remboursements."""
    
    list_display = [
        'payment_original', 'demandeur', 'montant_remboursement',
        'raison', 'statut', 'date_demande', 'traiteur'
    ]
    
    list_filter = ['statut', 'raison', 'date_demande', 'date_traitement']
    
    search_fields = [
        'payment_original__uuid', 'demandeur__username'
    ]
    
    readonly_fields = [
        'date_demande', 'date_traitement', 'date_remboursement'
    ]
    
    fieldsets = [
        (_('Demande'), {
            'fields': ('payment_original', 'demandeur', 'montant_remboursement')
        }),
        (_('Raison'), {
            'fields': ('raison', 'description')
        }),
        (_('Traitement'), {
            'fields': ('statut', 'traiteur', 'commentaire_admin')
        }),
        (_('Dates'), {
            'fields': ('date_demande', 'date_traitement', 'date_remboursement'),
            'classes': ('collapse',)
        }),
        (_('Paiement de remboursement'), {
            'fields': ('payment_remboursement',),
            'classes': ('collapse',)
        }),
    ]
    
    actions = ['approve_refunds', 'reject_refunds']
    
    def approve_refunds(self, request, queryset):
        """Approuve les demandes de remboursement."""
        updated = 0
        for refund in queryset.filter(statut='DEMANDE'):
            refund.approve(request.user, "Approuvé via l'interface admin")
            updated += 1
        
        self.message_user(request, f'{updated} remboursement(s) approuvé(s).')
    approve_refunds.short_description = _('Approuver les remboursements')
    
    def reject_refunds(self, request, queryset):
        """Rejette les demandes de remboursement."""
        updated = 0
        for refund in queryset.filter(statut='DEMANDE'):
            refund.reject(request.user, "Rejeté via l'interface admin")
            updated += 1
        
        self.message_user(request, f'{updated} remboursement(s) rejeté(s).')
    reject_refunds.short_description = _('Rejeter les remboursements')

