"""
Configuration de l'interface d'administration pour les événements.

Ce module configure l'affichage et les fonctionnalités de l'interface
d'administration Django pour les modèles liés aux événements.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db.models import Count, Sum
from .models import Event, EventCategory, EventParticipation, EventShare, EventTicket


@admin.register(EventCategory)
class EventCategoryAdmin(admin.ModelAdmin):
    """
    Interface d'administration pour les catégories d'événements.
    """
    
    list_display = ['nom', 'description', 'couleur', 'ordre', 'actif', 'get_events_count']
    list_editable = ['ordre', 'actif']
    list_filter = ['actif']
    search_fields = ['nom', 'description']
    ordering = ['ordre', 'nom']
    
    def get_events_count(self, obj):
        """Affiche le nombre d'événements dans cette catégorie."""
        count = obj.get_events_count()
        if count > 0:
            url = reverse('admin:events_event_changelist') + f'?categorie__id__exact={obj.id}'
            return format_html('<a href="{}">{} événements</a>', url, count)
        return '0 événement'
    get_events_count.short_description = _('Événements')


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    """
    Interface d'administration pour les événements.
    
    Interface principale pour la validation et la gestion des événements
    avec toutes les fonctionnalités de modération.
    """
    
    # Champs affichés dans la liste
    list_display = [
        'titre', 'createur', 'categorie', 'date_debut', 'statut',
        'get_participants_count', 'get_revenue', 'date_creation'
    ]
    
    # Champs de recherche
    search_fields = ['titre', 'description', 'lieu', 'createur__username']
    
    # Filtres latéraux
    list_filter = [
        'statut', 'categorie', 'type_acces', 'billetterie_activee',
        'date_debut', 'date_creation'
    ]
    
    # Champs modifiables directement dans la liste
    list_editable = ['statut']
    
    # Champs en lecture seule
    readonly_fields = [
        'date_creation', 'date_modification', 'nombre_vues', 'nombre_partages',
        'get_participants_count', 'get_revenue', 'get_commission_amount'
    ]
    
    # Organisation des champs
    fieldsets = [
        (_('Informations de base'), {
            'fields': ('titre', 'description', 'description_courte', 'categorie', 'createur')
        }),
        (_('Dates et lieu'), {
            'fields': ('date_debut', 'date_fin', 'lieu', 'adresse', 'latitude', 'longitude', 'lien_google_maps')
        }),
        (_('Accès et tarification'), {
            'fields': ('type_acces', 'prix', 'capacite_max')
        }),
        (_('Image'), {
            'fields': ('image_couverture',)
        }),
        (_('Billetterie'), {
            'fields': ('billetterie_activee', 'commission_billetterie'),
            'classes': ('collapse',)
        }),
        (_('Validation'), {
            'fields': ('statut', 'validateur', 'date_validation', 'commentaire_validation')
        }),
        (_('Statistiques'), {
            'fields': ('nombre_vues', 'nombre_partages', 'get_participants_count', 'get_revenue', 'get_commission_amount'),
            'classes': ('collapse',)
        }),
        (_('Métadonnées'), {
            'fields': ('date_creation', 'date_modification'),
            'classes': ('collapse',)
        }),
    ]
    
    # Actions personnalisées
    actions = ['approve_events', 'reject_events', 'mark_as_finished']
    
    # Filtres personnalisés
    def get_queryset(self, request):
        """Optimise les requêtes avec select_related et annotations."""
        return super().get_queryset(request).select_related(
            'createur', 'categorie', 'validateur'
        ).annotate(
            participants_count=Count('participations'),
            revenue=Sum('tickets__prix')
        )
    
    def get_participants_count(self, obj):
        """Affiche le nombre de participants."""
        count = obj.get_participants_count()
        if count > 0:
            url = reverse('admin:events_eventparticipation_changelist') + f'?evenement__id__exact={obj.id}'
            return format_html('<a href="{}">{} participants</a>', url, count)
        return '0 participant'
    get_participants_count.short_description = _('Participants')
    
    def get_revenue(self, obj):
        """Affiche le revenu de l'événement."""
        revenue = obj.get_revenue()
        if revenue > 0:
            return format_html('{:,.0f} FCFA', revenue)
        return '0 FCFA'
    get_revenue.short_description = _('Revenus')
    
    def get_commission_amount(self, obj):
        """Affiche le montant de commission."""
        commission = obj.get_commission_amount()
        if commission > 0:
            return format_html('{:,.0f} FCFA', commission)
        return '0 FCFA'
    get_commission_amount.short_description = _('Commission')
    
    def approve_events(self, request, queryset):
        """Action pour approuver des événements."""
        updated = 0
        for event in queryset.filter(statut='EN_ATTENTE'):
            event.statut = 'VALIDE'
            event.validateur = request.user
            event.date_validation = timezone.now()
            event.save()
            updated += 1
        
        self.message_user(
            request,
            f'{updated} événement(s) approuvé(s) avec succès.'
        )
    approve_events.short_description = _('Approuver les événements sélectionnés')
    
    def reject_events(self, request, queryset):
        """Action pour rejeter des événements."""
        updated = 0
        for event in queryset.filter(statut='EN_ATTENTE'):
            event.statut = 'REJETE'
            event.validateur = request.user
            event.date_validation = timezone.now()
            event.save()
            updated += 1
        
        self.message_user(
            request,
            f'{updated} événement(s) rejeté(s) avec succès.'
        )
    reject_events.short_description = _('Rejeter les événements sélectionnés')
    
    def mark_as_finished(self, request, queryset):
        """Action pour marquer des événements comme terminés."""
        updated = queryset.filter(statut='VALIDE').update(statut='TERMINE')
        self.message_user(
            request,
            f'{updated} événement(s) marqué(s) comme terminé(s).'
        )
    mark_as_finished.short_description = _('Marquer comme terminés')
    
    def save_model(self, request, obj, form, change):
        """Sauvegarde personnalisée pour enregistrer le validateur."""
        if change and 'statut' in form.changed_data:
            if obj.statut in ['VALIDE', 'REJETE']:
                obj.validateur = request.user
                obj.date_validation = timezone.now()
        
        super().save_model(request, obj, form, change)


@admin.register(EventParticipation)
class EventParticipationAdmin(admin.ModelAdmin):
    """
    Interface d'administration pour les participations aux événements.
    """
    
    list_display = [
        'utilisateur', 'evenement', 'statut', 'date_participation'
    ]
    
    list_filter = ['statut', 'date_participation', 'evenement__categorie']
    search_fields = [
        'utilisateur__username', 'utilisateur__email',
        'evenement__titre'
    ]
    
    readonly_fields = ['date_participation', 'date_modification']
    
    def get_queryset(self, request):
        """Optimise les requêtes."""
        return super().get_queryset(request).select_related(
            'utilisateur', 'evenement'
        )


@admin.register(EventShare)
class EventShareAdmin(admin.ModelAdmin):
    """
    Interface d'administration pour les partages d'événements.
    """
    
    list_display = [
        'utilisateur', 'evenement', 'plateforme', 'date_partage', 'nombre_clics'
    ]
    
    list_filter = ['plateforme', 'date_partage']
    search_fields = [
        'utilisateur__username', 'evenement__titre'
    ]
    
    readonly_fields = ['date_partage', 'lien_genere', 'nombre_clics']
    
    def get_queryset(self, request):
        """Optimise les requêtes."""
        return super().get_queryset(request).select_related(
            'utilisateur', 'evenement'
        )


@admin.register(EventTicket)
class EventTicketAdmin(admin.ModelAdmin):
    """
    Interface d'administration pour les billets d'événements.
    """
    
    list_display = [
        'uuid', 'evenement', 'utilisateur', 'prix', 'quantite',
        'statut', 'date_achat', 'get_qr_code'
    ]
    
    list_filter = ['statut', 'date_achat', 'evenement__categorie']
    search_fields = [
        'uuid', 'utilisateur__username', 'evenement__titre',
        'reference_paiement'
    ]
    
    readonly_fields = [
        'uuid', 'date_achat', 'date_utilisation', 'code_qr',
        'get_total_price'
    ]
    
    fieldsets = [
        (_('Informations de base'), {
            'fields': ('uuid', 'evenement', 'utilisateur', 'prix', 'quantite')
        }),
        (_('Statut'), {
            'fields': ('statut', 'date_achat', 'date_utilisation')
        }),
        (_('Paiement'), {
            'fields': ('reference_paiement',)
        }),
        (_('Code QR'), {
            'fields': ('code_qr',)
        }),
    ]
    
    def get_qr_code(self, obj):
        """Affiche le code QR s'il existe."""
        if obj.code_qr:
            return format_html(
                '<img src="{}" width="50" height="50" />',
                obj.code_qr.url
            )
        return '-'
    get_qr_code.short_description = _('Code QR')
    
    def get_total_price(self, obj):
        """Affiche le prix total."""
        return format_html('{:,.0f} FCFA', obj.get_total_price())
    get_total_price.short_description = _('Prix total')
    
    def get_queryset(self, request):
        """Optimise les requêtes."""
        return super().get_queryset(request).select_related(
            'utilisateur', 'evenement'
        )

