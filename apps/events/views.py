"""
Vues API pour l'application events.

Ce module définit les vues Django REST Framework pour
la gestion des événements et des interactions associées.
"""

from rest_framework import generics, status, permissions, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count, Sum
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from .models import Event, EventCategory, EventParticipation, EventShare, EventTicket
from .serializers import (
    EventCategorySerializer, EventCreateSerializer, EventSerializer,
    EventListSerializer, EventParticipationSerializer, EventParticipationCreateSerializer,
    EventShareSerializer, EventShareCreateSerializer, EventTicketSerializer,
    EventTicketCreateSerializer
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
        """Crée un billet d'événement."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        ticket = serializer.save()
        
        return Response({
            'message': 'Billet créé avec succès. Procédez au paiement.',
            'ticket': EventTicketSerializer(ticket).data
        }, status=status.HTTP_201_CREATED)


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

