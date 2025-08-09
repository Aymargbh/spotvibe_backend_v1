"""
Vues API pour l'application events.

Ce module définit les vues Django REST Framework pour
la gestion des événements et des interactions associées.
"""

import csv
from datetime import datetime, timedelta
from django.http import Http404, HttpResponse
from rest_framework import generics, status, permissions, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count, Sum
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from .models import Event, EventCategory, EventMedia, EventParticipation, EventShare, EventTicket
from .serializers import (
    EventCategorySerializer, EventCreateSerializer, EventDetailSerializer, EventMediaSerializer, EventMediaUploadSerializer, EventSerializer,
    EventListSerializer, EventParticipationSerializer, EventParticipationCreateSerializer,
    EventShareSerializer, EventShareCreateSerializer, EventTicketSerializer,
    EventTicketCreateSerializer, TrendingEventSerializer
)


class EventPagination(PageNumberPagination):
    """Pagination personnalisée pour les événements."""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class EventCategoryListView(generics.ListAPIView):
    """
    Vue pour lister les catégories d'événements.
    
    GET /api/events/categories/
    """
    
    serializer_class = EventCategorySerializer
    permission_classes = [permissions.AllowAny]
    queryset = EventCategory.objects.filter(actif=True).order_by('ordre', 'nom')


class EventCreateView(generics.CreateAPIView):
    """
    Vue pour créer un nouvel événement.
    
    POST /api/events/
    """
    
    serializer_class = EventCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        """Crée un nouvel événement."""
        if not request.user.can_create_event():
            return Response({
                'error': 'Vous n\'avez pas la permission de créer un événement. Vérifiez votre statut ou votre abonnement.'
            }, status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        event = serializer.save()
        
        return Response({
            'message': 'Événement créé avec succès. Il sera visible après validation par un administrateur.',
            'event': EventSerializer(event, context={'request': request}).data
        }, status=status.HTTP_201_CREATED)


class EventListView(generics.ListAPIView):
    """
    Vue pour lister les événements avec filtres et recherche.
    
    GET /api/events/
    """
    
    serializer_class = EventListSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = EventPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['categorie', 'type_acces', 'createur']
    search_fields = ['titre', 'description', 'lieu']
    ordering_fields = ['date_debut', 'date_creation', 'nombre_vues']
    ordering = ['date_debut']
    
    def get_queryset(self):
        """Retourne la liste des événements avec filtres."""
        queryset = Event.objects.filter(statut='VALIDE').select_related(
            'createur', 'categorie'
        ).annotate(
            participants_count=Count('participations')
        )
        
        # Filtrer par période
        periode = self.request.query_params.get('periode', None)
        now = timezone.now()
        
        if periode == 'today':
            queryset = queryset.filter(
                date_debut__date=now.date()
            )
        elif periode == 'week':
            end_week = now + timezone.timedelta(days=7)
            queryset = queryset.filter(
                date_debut__gte=now,
                date_debut__lte=end_week
            )
        elif periode == 'month':
            end_month = now + timezone.timedelta(days=30)
            queryset = queryset.filter(
                date_debut__gte=now,
                date_debut__lte=end_month
            )
        elif periode == 'past':
            queryset = queryset.filter(date_debut__lt=now)
        else:
            # Par défaut, événements futurs
            queryset = queryset.filter(date_debut__gte=now)
        
        # Filtrer par prix
        prix_max = self.request.query_params.get('prix_max', None)
        if prix_max:
            try:
                queryset = queryset.filter(prix__lte=float(prix_max))
            except ValueError:
                pass
        
        # Filtrer par proximité (si latitude et longitude fournies)
        lat = self.request.query_params.get('latitude', None)
        lng = self.request.query_params.get('longitude', None)
        rayon = self.request.query_params.get('rayon', 10)  # km
        
        if lat and lng:
            try:
                # Filtrage approximatif par coordonnées
                # Pour une implémentation plus précise, utiliser PostGIS
                lat_float = float(lat)
                lng_float = float(lng)
                rayon_float = float(rayon)
                
                # Approximation simple (1 degré ≈ 111 km)
                delta = rayon_float / 111.0
                
                queryset = queryset.filter(
                    latitude__gte=lat_float - delta,
                    latitude__lte=lat_float + delta,
                    longitude__gte=lng_float - delta,
                    longitude__lte=lng_float + delta
                )
            except ValueError:
                pass
        
        return queryset


class EventDetailView(generics.RetrieveAPIView):
    """
    Vue pour consulter les détails d'un événement.
    
    GET /api/events/{id}/
    """
    
    serializer_class = EventSerializer
    permission_classes = [permissions.AllowAny]
    queryset = Event.objects.filter(statut='VALIDE').select_related(
        'createur', 'categorie', 'validateur'
    )
    
    def retrieve(self, request, *args, **kwargs):
        """Récupère un événement et incrémente le compteur de vues."""
        instance = self.get_object()
        
        # Incrémenter le nombre de vues
        instance.nombre_vues += 1
        instance.save(update_fields=['nombre_vues'])
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class EventUpdateView(generics.UpdateAPIView):
    """
    Vue pour modifier un événement.
    
    PUT /api/events/{id}/
    PATCH /api/events/{id}/
    """
    
    serializer_class = EventCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Retourne les événements que l'utilisateur peut modifier."""
        if self.request.user.is_staff:
            return Event.objects.all()
        return Event.objects.filter(createur=self.request.user)
    
    def update(self, request, *args, **kwargs):
        """Met à jour un événement."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # Vérifier que l'événement peut être modifié
        if instance.statut == 'VALIDE' and instance.date_debut <= timezone.now():
            return Response({
                'error': 'Impossible de modifier un événement déjà commencé'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        # Remettre en attente si modifié après validation
        if instance.statut == 'VALIDE':
            instance.statut = 'EN_ATTENTE'
            instance.validateur = None
            instance.date_validation = None
        
        self.perform_update(serializer)
        
        return Response({
            'message': 'Événement modifié avec succès',
            'event': EventSerializer(instance, context={'request': request}).data
        })


class EventDeleteView(generics.DestroyAPIView):
    """
    Vue pour supprimer un événement.
    
    DELETE /api/events/{id}/
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Retourne les événements que l'utilisateur peut supprimer."""
        if self.request.user.is_staff:
            return Event.objects.all()
        return Event.objects.filter(createur=self.request.user)
    
    def destroy(self, request, *args, **kwargs):
        """Supprime un événement."""
        instance = self.get_object()
        
        # Vérifier qu'il n'y a pas de billets vendus
        if instance.tickets.filter(statut__in=['VALIDE', 'UTILISE']).exists():
            return Response({
                'error': 'Impossible de supprimer un événement avec des billets vendus'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        self.perform_destroy(instance)
        return Response({
            'message': 'Événement supprimé avec succès'
        }, status=status.HTTP_204_NO_CONTENT)


class EventParticipationView(generics.CreateAPIView):
    """
    Vue pour participer à un événement.
    
    POST /api/events/participate/
    """
    
    serializer_class = EventParticipationCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        """Crée ou met à jour une participation."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        participation = serializer.save()
        
        return Response({
            'message': 'Participation enregistrée avec succès',
            'participation': EventParticipationSerializer(participation).data
        }, status=status.HTTP_201_CREATED)


@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def cancel_participation_view(request, event_id):
    """
    Vue pour annuler une participation.
    
    DELETE /api/events/{event_id}/cancel-participation/
    """
    
    try:
        event = Event.objects.get(id=event_id, statut='VALIDE')
    except Event.DoesNotExist:
        return Response({
            'error': 'Événement introuvable'
        }, status=status.HTTP_404_NOT_FOUND)
    
    try:
        participation = EventParticipation.objects.get(
            utilisateur=request.user,
            evenement=event
        )
        participation.delete()
        
        return Response({
            'message': 'Participation annulée avec succès'
        }, status=status.HTTP_200_OK)
        
    except EventParticipation.DoesNotExist:
        return Response({
            'error': 'Vous ne participez pas à cet événement'
        }, status=status.HTTP_400_BAD_REQUEST)


class EventParticipantsView(generics.ListAPIView):
    """
    Vue pour lister les participants d'un événement.
    
    GET /api/events/{event_id}/participants/
    """
    
    serializer_class = EventParticipationSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = EventPagination
    
    def get_queryset(self):
        """Retourne les participants de l'événement."""
        event_id = self.kwargs['event_id']
        return EventParticipation.objects.filter(
            evenement_id=event_id,
            statut='CONFIRME'
        ).select_related('utilisateur', 'evenement').order_by('-date_participation')


class EventShareView(generics.CreateAPIView):
    """
    Vue pour partager un événement.
    
    POST /api/events/share/
    """
    
    serializer_class = EventShareCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        """Crée un partage d'événement."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        share = serializer.save()
        
        return Response({
            'message': 'Événement partagé avec succès',
            'share': EventShareSerializer(share).data
        }, status=status.HTTP_201_CREATED)


class EventTicketPurchaseView(generics.CreateAPIView):
    """
    Vue pour acheter un billet d'événement.
    
    POST /api/events/tickets/purchase/
    """
    
    serializer_class = EventTicketCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        """Crée un billet d'événement et initie le paiement."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        ticket = serializer.save(utilisateur=request.user) # Assigner l'utilisateur courant
        
        # Créer une instance de paiement liée au billet
        try:
            payment = Payment.objects.create(
                utilisateur=request.user,
                montant=ticket.prix_total,
                type_paiement='BILLET_EVENEMENT',
                statut='EN_ATTENTE',
                objet_concerne=ticket # Lier le paiement au billet
            )
            payment_serializer = PaymentSerializer(payment) # Sérialiseur pour le paiement
            
            return Response({
                'message': 'Billet créé avec succès. Procédez au paiement.',
                'ticket': EventTicketSerializer(ticket).data,
                'payment': payment_serializer.data # Retourner les détails du paiement
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            ticket.delete() # Annuler la création du billet si le paiement échoue
            return Response({
                'error': f'Erreur lors de l\'initialisation du paiement: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserEventsView(generics.ListAPIView):
    """
    Vue pour lister les événements d'un utilisateur.
    
    GET /api/events/my-events/
    """
    
    serializer_class = EventListSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = EventPagination
    
    def get_queryset(self):
        """Retourne les événements créés par l'utilisateur."""
        return Event.objects.filter(
            createur=self.request.user
        ).select_related('categorie').order_by('-date_creation')


class UserParticipationsView(generics.ListAPIView):
    """
    Vue pour lister les participations d'un utilisateur.
    
    GET /api/events/my-participations/
    """
    
    serializer_class = EventParticipationSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = EventPagination
    
    def get_queryset(self):
        """Retourne les participations de l'utilisateur."""
        return EventParticipation.objects.filter(
            utilisateur=self.request.user
        ).select_related('evenement', 'evenement__categorie').order_by('-date_participation')


class UserTicketsView(generics.ListAPIView):
    """
    Vue pour lister les billets d'un utilisateur.
    
    GET /api/events/my-tickets/
    """
    
    serializer_class = EventTicketSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = EventPagination
    
    def get_queryset(self):
        """Retourne les billets de l'utilisateur."""
        return EventTicket.objects.filter(
            utilisateur=self.request.user
        ).select_related('evenement').order_by('-date_achat')


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def event_stats_view(request):
    """
    Vue pour obtenir les statistiques des événements.
    
    GET /api/events/stats/
    """
    
    now = timezone.now()
    
    stats = {
        'total_events': Event.objects.filter(statut='VALIDE').count(),
        'events_today': Event.objects.filter(
            statut='VALIDE',
            date_debut__date=now.date()
        ).count(),
        'events_this_week': Event.objects.filter(
            statut='VALIDE',
            date_debut__gte=now,
            date_debut__lte=now + timezone.timedelta(days=7)
        ).count(),
        'events_this_month': Event.objects.filter(
            statut='VALIDE',
            date_debut__gte=now,
            date_debut__lte=now + timezone.timedelta(days=30)
        ).count(),
        'total_participants': EventParticipation.objects.filter(
            statut='CONFIRME'
        ).count(),
        'categories': EventCategorySerializer(
            EventCategory.objects.filter(actif=True).order_by('ordre'),
            many=True
        ).data
    }
    
    return Response(stats, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def trending_events_view(request):
    """
    Vue pour obtenir les événements tendance.
    
    GET /api/events/trending/
    """
    
    # Événements avec le plus de participants récents
    trending = Event.objects.filter(
        statut='VALIDE',
        date_debut__gte=timezone.now()
    ).annotate(
        participants_count=Count('participations')
    ).order_by('-participants_count', '-nombre_vues')[:10]
    
    serializer = EventListSerializer(trending, many=True, context={'request': request})
    
    return Response({
        'trending_events': serializer.data
    }, status=status.HTTP_200_OK)


# ===== VUES MANQUANTES POUR LES BILLETS =====

class EventTicketDetailView(generics.RetrieveAPIView):
    """
    Vue pour consulter les détails d'un billet.
    
    GET /api/events/tickets/{uuid}/
    """
    
    serializer_class = EventTicketSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'uuid'
    
    def get_queryset(self):
        """Retourne les billets de l'utilisateur ou tous si admin."""
        if self.request.user.is_staff:
            return EventTicket.objects.all()
        return EventTicket.objects.filter(utilisateur=self.request.user)


class EventTicketListView(generics.ListAPIView):
    """
    Vue pour lister les billets d'un événement.
    
    GET /api/events/{event_id}/tickets/
    """
    
    serializer_class = EventTicketSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = EventPagination
    
    def get_queryset(self):
        """Retourne les billets de l'événement."""
        event_id = self.kwargs['event_id']
        
        # Vérifier que l'utilisateur peut voir ces billets
        try:
            event = Event.objects.get(id=event_id)
        except Event.DoesNotExist:
            return EventTicket.objects.none()
        
        # Seul le créateur de l'événement ou un admin peut voir tous les billets
        if event.createur != self.request.user and not self.request.user.is_staff:
            return EventTicket.objects.none()
        
        return EventTicket.objects.filter(
            evenement_id=event_id
        ).select_related('utilisateur', 'evenement').order_by('-date_achat')


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def validate_ticket(request, uuid):
    """
    Vue pour valider un billet lors de l'entrée à l'événement.
    
    POST /api/events/tickets/{uuid}/validate/
    """
    
    try:
        ticket = EventTicket.objects.get(uuid=uuid)
    except EventTicket.DoesNotExist:
        return Response({
            'error': 'Billet introuvable'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Vérifier que l'utilisateur peut valider ce billet
    event = ticket.evenement
    if event.createur != request.user and not request.user.is_staff:
        return Response({
            'error': 'Permission refusée'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Vérifier le statut du billet
    if ticket.statut != 'VALIDE':
        return Response({
            'error': f'Billet non valide (statut: {ticket.get_statut_display()})'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Vérifier que l'événement n'est pas passé
    if event.date_fin < timezone.now():
        return Response({
            'error': 'Événement terminé'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Valider le billet
    ticket.statut = 'UTILISE'
    ticket.date_utilisation = timezone.now()
    ticket.save()
    
    return Response({
        'message': 'Billet validé avec succès',
        'ticket': EventTicketSerializer(ticket).data
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def track_share_click(request, pk):
    """
    Vue pour tracker les clics sur les liens de partage.
    
    POST /api/events/shares/{pk}/click/
    """
    
    try:
        share = EventShare.objects.get(id=pk)
    except EventShare.DoesNotExist:
        return Response({
            'error': 'Partage introuvable'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Incrémenter le compteur de clics
    share.nombre_clics += 1
    share.save()
    
    # Rediriger vers l'événement
    event_url = f"/events/{share.evenement.id}/"
    
    return Response({
        'message': 'Clic enregistré',
        'redirect_url': event_url
    }, status=status.HTTP_200_OK)



class EventSearchView(generics.ListAPIView):
    """
    Vue pour la recherche avancée d'événements.
    
    GET /api/events/search/?q=terme&category=1&location=ville&date_from=2024-01-01&date_to=2024-12-31
    """
    
    serializer_class = EventSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = PageNumberPagination
    
    def get_queryset(self):
        """Retourne les événements filtrés selon les critères de recherche."""
        queryset = Event.objects.filter(statut='VALIDE')
        
        # Recherche textuelle
        q = self.request.query_params.get('q', '')
        if q:
            queryset = queryset.filter(
                Q(titre__icontains=q) |
                Q(description__icontains=q) |
                Q(lieu__icontains=q) |
                Q(adresse__icontains=q)
            )
        
        # Filtrer par catégorie
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(categorie_id=category)
        
        # Filtrer par localisation
        location = self.request.query_params.get('location')
        if location:
            queryset = queryset.filter(
                Q(lieu__icontains=location) |
                Q(adresse__icontains=location)
            )
        
        # Filtrer par dates
        date_from = self.request.query_params.get('date_from')
        if date_from:
            try:
                date_from = datetime.fromisoformat(date_from)
                queryset = queryset.filter(date_debut__gte=date_from)
            except ValueError:
                pass
        
        date_to = self.request.query_params.get('date_to')
        if date_to:
            try:
                date_to = datetime.fromisoformat(date_to)
                queryset = queryset.filter(date_fin__lte=date_to)
            except ValueError:
                pass
        
        # Filtrer par prix
        prix_min = self.request.query_params.get('prix_min')
        if prix_min:
            try:
                queryset = queryset.filter(prix__gte=float(prix_min))
            except ValueError:
                pass
        
        prix_max = self.request.query_params.get('prix_max')
        if prix_max:
            try:
                queryset = queryset.filter(prix__lte=float(prix_max))
            except ValueError:
                pass
        
        # Filtrer par type d'accès
        type_acces = self.request.query_params.get('type_acces')
        if type_acces in ['GRATUIT', 'PAYANT', 'INVITATION']:
            queryset = queryset.filter(type_acces=type_acces)
        
        # Trier les résultats
        sort_by = self.request.query_params.get('sort', 'date_debut')
        if sort_by in ['date_debut', '-date_debut', 'prix', '-prix', 'nombre_vues', '-nombre_vues']:
            queryset = queryset.order_by(sort_by)
        else:
            queryset = queryset.order_by('date_debut')
        
        return queryset


class NearbyEventsView(generics.ListAPIView):
    """
    Vue pour trouver les événements à proximité.
    
    GET /api/events/nearby/?lat=6.1319&lng=1.2228&radius=10
    """
    
    serializer_class = EventSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = PageNumberPagination
    
    def get_queryset(self):
        """Retourne les événements à proximité des coordonnées données."""
        lat = self.request.query_params.get('lat')
        lng = self.request.query_params.get('lng')
        radius = self.request.query_params.get('radius', '10')  # Rayon en km
        
        if not lat or not lng:
            return Event.objects.none()
        
        try:
            lat = float(lat)
            lng = float(lng)
            radius = float(radius)
        except ValueError:
            return Event.objects.none()
        
        # Calcul approximatif de la distance (formule simple)
        # Pour une précision plus élevée, utiliser une bibliothèque comme geopy
        lat_range = radius / 111.0  # 1 degré ≈ 111 km
        lng_range = radius / (111.0 * abs(lat))
        
        queryset = Event.objects.filter(
            statut='VALIDE',
            latitude__isnull=False,
            longitude__isnull=False,
            latitude__range=(lat - lat_range, lat + lat_range),
            longitude__range=(lng - lng_range, lng + lng_range)
        ).order_by('date_debut')
        
        return queryset


class EventRecommendationsView(generics.ListAPIView):
    """
    Vue pour les recommandations d'événements personnalisées.
    
    GET /api/events/recommendations/
    """
    
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = PageNumberPagination
    
    def get_queryset(self):
        """Retourne des événements recommandés basés sur l'historique de l'utilisateur."""
        user = self.request.user
        
        # Récupérer les catégories d'événements auxquels l'utilisateur a participé
        user_categories = EventParticipation.objects.filter(
            utilisateur=user
        ).values_list('evenement__categorie', flat=True).distinct()
        
        # Recommander des événements dans ces catégories
        queryset = Event.objects.filter(
            statut='VALIDE',
            date_debut__gt=timezone.now(),
            categorie__in=user_categories
        ).exclude(
            # Exclure les événements auxquels l'utilisateur participe déjà
            participations__utilisateur=user
        ).order_by('-nombre_vues', 'date_debut')
        
        # Si pas assez de recommandations, ajouter des événements populaires
        if queryset.count() < 10:
            popular_events = Event.objects.filter(
                statut='VALIDE',
                date_debut__gt=timezone.now()
            ).exclude(
                participations__utilisateur=user
            ).order_by('-nombre_vues')[:20]
            
            # Combiner les deux querysets
            queryset = queryset.union(popular_events)
        
        return queryset


class PendingEventsView(generics.ListAPIView):
    """
    Vue pour lister les événements en attente de validation.
    
    GET /api/events/pending-approval/
    """
    
    serializer_class = EventDetailSerializer
    permission_classes = [permissions.IsAdminUser]
    pagination_class = PageNumberPagination
    
    def get_queryset(self):
        """Retourne les événements en attente de validation."""
        return Event.objects.filter(
            statut='EN_ATTENTE'
        ).order_by('date_creation')


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def event_stats_view(request):
    """
    Vue pour obtenir les statistiques générales des événements.
    
    GET /api/events/stats/
    """
    
    # Statistiques de base
    total_events = Event.objects.filter(statut='VALIDE').count()
    upcoming_events = Event.objects.filter(
        statut='VALIDE',
        date_debut__gt=timezone.now()
    ).count()
    
    past_events = Event.objects.filter(
        statut='VALIDE',
        date_fin__lt=timezone.now()
    ).count()
    
    # Événements par catégorie
    events_by_category = list(
        EventCategory.objects.annotate(
            count=Count('events', filter=Q(events__statut='VALIDE'))
        ).values('nom', 'count')
    )
    
    # Événements par mois (12 derniers mois)
    now = timezone.now()
    events_by_month = []
    for i in range(12):
        month_start = now.replace(day=1) - timedelta(days=30*i)
        month_end = month_start.replace(day=28) + timedelta(days=4)
        month_end = month_end - timedelta(days=month_end.day)
        
        count = Event.objects.filter(
            statut='VALIDE',
            date_creation__range=(month_start, month_end)
        ).count()
        
        events_by_month.append({
            'month': month_start.strftime('%Y-%m'),
            'count': count
        })
    
    events_by_month.reverse()
    
    # Événements les plus populaires
    popular_events = Event.objects.filter(
        statut='VALIDE'
    ).order_by('-nombre_vues')[:5].values(
        'id', 'titre', 'nombre_vues', 'date_debut'
    )
    
    stats = {
        'total_events': total_events,
        'upcoming_events': upcoming_events,
        'past_events': past_events,
        'events_by_category': events_by_category,
        'events_by_month': events_by_month,
        'popular_events': list(popular_events)
    }
    
    return Response(stats, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def trending_events_view(request):
    """
    Vue pour obtenir les événements tendance.
    
    GET /api/events/trending/
    """
    
    # Calculer le score de tendance basé sur les vues et participations récentes
    last_week = timezone.now() - timedelta(days=7)
    
    trending_events = Event.objects.filter(
        statut='VALIDE',
        date_debut__gt=timezone.now()
    ).annotate(
        recent_participations=Count(
            'participations',
            filter=Q(participations__date_participation__gte=last_week)
        ),
        total_participations=Count('participations')
    ).order_by(
        '-recent_participations',
        '-nombre_vues',
        '-total_participations'
    )[:10]
    
    serializer = TrendingEventSerializer(trending_events, many=True)
    
    return Response({
        'trending_events': serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def event_analytics(request, event_id):
    """
    Vue pour obtenir les analytics détaillées d'un événement.
    
    GET /api/events/{event_id}/analytics/
    """
    
    try:
        event = Event.objects.get(id=event_id)
    except Event.DoesNotExist:
        return Response({
            'error': 'Événement introuvable'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Vérifier les permissions
    if event.createur != request.user and not request.user.is_staff:
        return Response({
            'error': 'Permission refusée'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Statistiques de participation
    total_participants = event.get_participants_count()
    total_interested = event.get_interested_count()
    
    # Évolution des participations dans le temps
    participations_by_day = list(
        EventParticipation.objects.filter(
            evenement=event
        ).extra(
            select={'day': 'date(date_participation)'}
        ).values('day').annotate(
            count=Count('id')
        ).order_by('day')
    )
    
    # Statistiques de partage
    total_shares = event.partages.count()
    shares_by_platform = list(
        event.partages.values('plateforme').annotate(
            count=Count('id')
        ).order_by('-count')
    )
    
    # Revenus de billetterie
    revenue_data = {
        'total_revenue': event.get_revenue(),
        'commission_amount': event.get_commission_amount(),
        'tickets_sold': event.tickets.filter(statut='PAYE').count()
    }
    
    analytics = {
        'event_id': event.id,
        'event_title': event.titre,
        'views': event.nombre_vues,
        'participants': {
            'total_participants': total_participants,
            'total_interested': total_interested,
            'participations_by_day': participations_by_day
        },
        'shares': {
            'total_shares': total_shares,
            'shares_by_platform': shares_by_platform
        },
        'revenue': revenue_data
    }
    
    return Response(analytics, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([permissions.IsAdminUser])
def approve_event(request, event_id):
    """
    Vue pour approuver un événement.
    
    POST /api/events/{event_id}/approve/
    """
    
    try:
        event = Event.objects.get(id=event_id)
    except Event.DoesNotExist:
        return Response({
            'error': 'Événement introuvable'
        }, status=status.HTTP_404_NOT_FOUND)
    
    if event.statut != 'EN_ATTENTE':
        return Response({
            'error': 'Cet événement ne peut pas être approuvé'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Approuver l'événement
    event.statut = 'VALIDE'
    event.date_validation = timezone.now()
    event.validateur = request.user
    event.commentaire_validation = request.data.get('commentaire', '')
    event.save()
    
    return Response({
        'message': 'Événement approuvé avec succès'
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([permissions.IsAdminUser])
def reject_event(request, event_id):
    """
    Vue pour rejeter un événement.
    
    POST /api/events/{event_id}/reject/
    """
    
    try:
        event = Event.objects.get(id=event_id)
    except Event.DoesNotExist:
        return Response({
            'error': 'Événement introuvable'
        }, status=status.HTTP_404_NOT_FOUND)
    
    if event.statut != 'EN_ATTENTE':
        return Response({
            'error': 'Cet événement ne peut pas être rejeté'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Rejeter l'événement
    event.statut = 'REJETE'
    event.date_validation = timezone.now()
    event.validateur = request.user
    event.commentaire_validation = request.data.get('commentaire', 'Événement rejeté')
    event.save()
    
    return Response({
        'message': 'Événement rejeté'
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def export_participants(request, event_id):
    """
    Vue pour exporter la liste des participants en CSV.
    
    GET /api/events/{event_id}/export-participants/
    """
    
    try:
        event = Event.objects.get(id=event_id)
    except Event.DoesNotExist:
        return Response({
            'error': 'Événement introuvable'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Vérifier les permissions
    if event.createur != request.user and not request.user.is_staff:
        return Response({
            'error': 'Permission refusée'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Créer la réponse CSV
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="participants_{event.id}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Nom', 'Email', 'Téléphone', 'Statut', 'Date de participation'])
    
    # Exporter les participants
    participants = EventParticipation.objects.filter(
        evenement=event
    ).select_related('utilisateur')
    
    for participation in participants:
        user = participation.utilisateur
        writer.writerow([
            user.get_full_name() or user.username,
            user.email,
            getattr(user, 'telephone', ''),
            participation.get_statut_display(),
            participation.date_participation.strftime('%d/%m/%Y %H:%M')
        ])
    
    return response


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def generate_event_report(request, event_id):
    """
    Vue pour générer un rapport détaillé d'un événement.
    
    GET /api/events/{event_id}/generate-report/
    """
    
    try:
        event = Event.objects.get(id=event_id)
    except Event.DoesNotExist:
        return Response({
            'error': 'Événement introuvable'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Vérifier les permissions
    if event.createur != request.user and not request.user.is_staff:
        return Response({
            'error': 'Permission refusée'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Générer le rapport
    report = {
        'event_info': {
            'id': event.id,
            'title': event.titre,
            'description': event.description,
            'date_debut': event.date_debut,
            'date_fin': event.date_fin,
            'lieu': event.lieu,
            'adresse': event.adresse,
            'statut': event.get_statut_display(),
            'type_acces': event.get_type_acces_display(),
            'prix': float(event.prix),
            'capacite_max': event.capacite_max
        },
        'statistics': {
            'views': event.nombre_vues,
            'shares': event.nombre_partages,
            'participants': event.get_participants_count(),
            'interested': event.get_interested_count(),
            'revenue': float(event.get_revenue()),
            'commission': float(event.get_commission_amount())
        },
        'participations': list(
            event.participations.values(
                'utilisateur__username',
                'utilisateur__email',
                'statut',
                'date_participation'
            )
        ),
        'tickets_sold': list(
            event.tickets.filter(statut='PAYE').values(
                'nom',
                'prix',
                'quantite',
                'date_achat'
            )
        ),
        'generated_at': timezone.now()
    }
    
    return Response(report, status=status.HTTP_200_OK)


class EventMediaPagination(PageNumberPagination):
    """Pagination personnalisée pour les médias d'événements."""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 50


class EventMediaListView(generics.ListAPIView):
    """
    Vue pour lister les médias d'un événement.
    
    GET /api/events/{event_id}/medias/
    """
    
    serializer_class = EventMediaSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = EventMediaPagination
    
    def get_queryset(self):
        """Retourne les médias de l'événement."""
        event_id = self.kwargs['event_id']
        
        # Vérifier que l'événement existe
        try:
            event = Event.objects.get(id=event_id)
        except Event.DoesNotExist:
            raise Http404("Événement introuvable")
        
        # Filtrer les médias selon les permissions
        queryset = EventMedia.objects.filter(
            evenement_id=event_id,
            est_active=True
        ).order_by('ordre', 'date_upload')
        
        # Filtrer par type de média si spécifié
        type_media = self.request.query_params.get('type')
        if type_media in ['image', 'video']:
            queryset = queryset.filter(type_media=type_media)
        
        # Filtrer par usage si spécifié
        usage = self.request.query_params.get('usage')
        if usage in ['galerie', 'couverture', 'post_cover', 'thumbnail']:
            queryset = queryset.filter(usage=usage)
        
        return queryset


class EventMediaUploadView(generics.CreateAPIView):
    """
    Vue pour uploader un média vers un événement.
    
    POST /api/events/{event_id}/medias/upload/
    """
    
    serializer_class = EventMediaUploadSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        """Upload un nouveau média."""
        event_id = self.kwargs['event_id']
        
        # Vérifier que l'événement existe et que l'utilisateur peut le modifier
        try:
            event = Event.objects.get(id=event_id)
        except Event.DoesNotExist:
            return Response({
                'error': 'Événement introuvable'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Vérifier les permissions
        if event.createur != request.user and not request.user.is_staff:
            return Response({
                'error': 'Permission refusée'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Ajouter l'événement aux données
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Créer le média
        media = serializer.save(
            evenement=event,
            uploade_par=request.user
        )
        
        return Response({
            'message': 'Média uploadé avec succès',
            'media': EventMediaSerializer(media).data
        }, status=status.HTTP_201_CREATED)


class EventMediaDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Vue pour consulter, modifier ou supprimer un média.
    
    GET /api/events/medias/{id}/
    PUT /api/events/medias/{id}/
    DELETE /api/events/medias/{id}/
    """
    
    serializer_class = EventMediaSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Retourne les médias que l'utilisateur peut modifier."""
        if self.request.user.is_staff:
            return EventMedia.objects.all()
        
        return EventMedia.objects.filter(
            evenement__createur=self.request.user
        )
    
    def destroy(self, request, *args, **kwargs):
        """Supprime un média."""
        instance = self.get_object()
        
        # Marquer comme inactif plutôt que supprimer
        instance.est_active = False
        instance.save()
        
        return Response({
            'message': 'Média supprimé avec succès'
        }, status=status.HTTP_204_NO_CONTENT)


class EventMediaDeleteView(generics.DestroyAPIView):
    """
    Vue pour supprimer définitivement un média.
    
    DELETE /api/events/medias/{id}/delete/
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Retourne les médias que l'utilisateur peut supprimer."""
        if self.request.user.is_staff:
            return EventMedia.objects.all()
        
        return EventMedia.objects.filter(
            evenement__createur=self.request.user
        )
    
    def destroy(self, request, *args, **kwargs):
        """Supprime définitivement un média."""
        instance = self.get_object()
        
        # Supprimer les fichiers physiques
        if instance.fichier:
            instance.fichier.delete(save=False)
        if instance.thumbnail:
            instance.thumbnail.delete(save=False)
        
        # Supprimer l'enregistrement
        instance.delete()
        
        return Response({
            'message': 'Média supprimé définitivement'
        }, status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def set_cover_image(request, event_id, media_id):
    """
    Vue pour définir l'image de couverture d'un événement.
    
    POST /api/events/{event_id}/set-cover/{media_id}/
    """
    
    try:
        event = Event.objects.get(id=event_id)
    except Event.DoesNotExist:
        return Response({
            'error': 'Événement introuvable'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Vérifier les permissions
    if event.createur != request.user and not request.user.is_staff:
        return Response({
            'error': 'Permission refusée'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Définir l'image de couverture
    if event.set_cover_image(media_id):
        return Response({
            'message': 'Image de couverture définie avec succès'
        }, status=status.HTTP_200_OK)
    else:
        return Response({
            'error': 'Média introuvable ou invalide'
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def set_post_cover_image(request, event_id, media_id):
    """
    Vue pour définir l'image de couverture pour les posts.
    
    POST /api/events/{event_id}/set-post-cover/{media_id}/
    """
    
    try:
        event = Event.objects.get(id=event_id)
    except Event.DoesNotExist:
        return Response({
            'error': 'Événement introuvable'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Vérifier les permissions
    if event.createur != request.user and not request.user.is_staff:
        return Response({
            'error': 'Permission refusée'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Définir l'image de couverture pour les posts
    if event.set_post_cover_image(media_id):
        return Response({
            'message': 'Image de couverture pour les posts définie avec succès'
        }, status=status.HTTP_200_OK)
    else:
        return Response({
            'error': 'Média introuvable ou invalide'
        }, status=status.HTTP_400_BAD_REQUEST)

