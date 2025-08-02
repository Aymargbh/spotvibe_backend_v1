"""
Vues pour l'application notifications.

Ce module définit les vues Django REST Framework pour
le système de notifications.
"""

from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Count, Q
from django.utils import timezone
from django.shortcuts import get_object_or_404
from .models import (
    Notification, NotificationPreference, NotificationTemplate,
    PushToken
)
from .serializers import (
    NotificationSerializer, NotificationCreateSerializer,
    NotificationTemplateSerializer, NotificationPreferenceSerializer,
    NotificationPreferenceUpdateSerializer, PushTokenSerializer,
    PushTokenCreateSerializer, NotificationStatsSerializer,
    BulkNotificationSerializer, NotificationMarkReadSerializer
)


class NotificationPagination(PageNumberPagination):
    """Pagination personnalisée pour les notifications."""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class NotificationListView(generics.ListAPIView):
    """
    Vue pour lister les notifications de l'utilisateur.
    
    GET /api/notifications/
    """
    
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = NotificationPagination
    
    def get_queryset(self):
        """Retourne les notifications de l'utilisateur."""
        queryset = Notification.objects.filter(
            destinataire=self.request.user
        ).order_by('-date_creation')
        
        # Filtrer par statut
        statut = self.request.query_params.get('statut')
        if statut:
            queryset = queryset.filter(statut=statut)
        
        # Filtrer par type
        type_notification = self.request.query_params.get('type')
        if type_notification:
            queryset = queryset.filter(type_notification=type_notification)
        
        return queryset


class NotificationDetailView(generics.RetrieveUpdateAPIView):
    """
    Vue pour consulter et modifier une notification.
    
    GET /api/notifications/{id}/
    PUT /api/notifications/{id}/
    """
    
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Retourne les notifications de l'utilisateur."""
        return Notification.objects.filter(destinataire=self.request.user)
    
    def retrieve(self, request, *args, **kwargs):
        """Marque la notification comme lue lors de la consultation."""
        instance = self.get_object()
        
        # Marquer comme lue si ce n'est pas déjà fait
        if instance.statut == 'NOUVEAU':
            instance.statut = 'LU'
            instance.date_lecture = timezone.now()
            instance.save()
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def mark_notifications_read(request):
    """
    Vue pour marquer des notifications comme lues.
    
    POST /api/notifications/mark-read/
    """
    
    serializer = NotificationMarkReadSerializer(
        data=request.data,
        context={'request': request}
    )
    serializer.is_valid(raise_exception=True)
    
    notification_ids = serializer.validated_data['notification_ids']
    
    # Marquer les notifications comme lues
    updated_count = Notification.objects.filter(
        id__in=notification_ids,
        destinataire=request.user,
        statut='NOUVEAU'
    ).update(
        statut='LU',
        date_lecture=timezone.now()
    )
    
    return Response({
        'message': f'{updated_count} notifications marquées comme lues'
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def mark_all_read(request):
    """
    Vue pour marquer toutes les notifications comme lues.
    
    POST /api/notifications/mark-all-read/
    """
    
    updated_count = Notification.objects.filter(
        destinataire=request.user,
        statut='NOUVEAU'
    ).update(
        statut='LU',
        date_lecture=timezone.now()
    )
    
    return Response({
        'message': f'{updated_count} notifications marquées comme lues'
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def notification_stats(request):
    """
    Vue pour obtenir les statistiques de notifications.
    
    GET /api/notifications/stats/
    """
    
    user = request.user
    
    # Statistiques de base
    total_notifications = Notification.objects.filter(destinataire=user).count()
    unread_notifications = Notification.objects.filter(
        destinataire=user,
        statut='NOUVEAU'
    ).count()
    
    # Notifications aujourd'hui
    today = timezone.now().date()
    notifications_today = Notification.objects.filter(
        destinataire=user,
        date_creation__date=today
    ).count()
    
    # Notifications par type
    notifications_by_type = dict(
        Notification.objects.filter(destinataire=user)
        .values('type_notification')
        .annotate(count=Count('id'))
        .values_list('type_notification', 'count')
    )
    
    # Notifications par statut
    notifications_by_status = dict(
        Notification.objects.filter(destinataire=user)
        .values('statut')
        .annotate(count=Count('id'))
        .values_list('statut', 'count')
    )
    
    stats_data = {
        'total_notifications': total_notifications,
        'unread_notifications': unread_notifications,
        'notifications_today': notifications_today,
        'notifications_by_type': notifications_by_type,
        'notifications_by_status': notifications_by_status
    }
    
    return Response(stats_data, status=status.HTTP_200_OK)


class NotificationPreferenceView(generics.RetrieveUpdateAPIView):
    """
    Vue pour consulter et modifier les préférences de notifications.
    
    GET /api/notifications/preferences/
    PUT /api/notifications/preferences/
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        """Retourne le sérialiseur approprié selon la méthode."""
        if self.request.method in ['PUT', 'PATCH']:
            return NotificationPreferenceUpdateSerializer
        return NotificationPreferenceSerializer
    
    def get_object(self):
        """Retourne ou crée les préférences de l'utilisateur."""
        preference, created = NotificationPreference.objects.get_or_create(
            utilisateur=self.request.user
        )
        return preference


class NotificationTemplateListView(generics.ListAPIView):
    """
    Vue pour lister les templates de notifications.
    
    GET /api/notifications/templates/
    """
    
    serializer_class = NotificationTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Retourne les templates actifs."""
        return NotificationTemplate.objects.filter(actif=True).order_by('nom')


class PushTokenListView(generics.ListCreateAPIView):
    """
    Vue pour lister et créer des tokens push.
    
    GET /api/notifications/push-tokens/
    POST /api/notifications/push-tokens/
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        """Retourne le sérialiseur approprié selon la méthode."""
        if self.request.method == 'POST':
            return PushTokenCreateSerializer
        return PushTokenSerializer
    
    def get_queryset(self):
        """Retourne les tokens de l'utilisateur."""
        return PushToken.objects.filter(
            utilisateur=self.request.user,
            actif=True
        ).order_by('-date_creation')


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def send_bulk_notification(request):
    """
    Vue pour envoyer des notifications en masse.
    
    POST /api/notifications/bulk-send/
    """
    
    if not request.user.is_staff:
        return Response({
            'error': 'Permission refusée'
        }, status=status.HTTP_403_FORBIDDEN)
    
    serializer = BulkNotificationSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    try:
        data = serializer.validated_data
        destinataires_ids = data['destinataires']
        
        # Créer les notifications
        notifications = []
        for destinataire_id in destinataires_ids:
            notification = Notification(
                destinataire_id=destinataire_id,
                titre=data['titre'],
                message=data['message'],
                type_notification=data['type_notification'],
                canal=data['canal'],
                donnees_supplementaires=data.get('donnees_supplementaires'),
                lien_action=data.get('lien_action')
            )
            notifications.append(notification)
        
        # Créer en lot
        Notification.objects.bulk_create(notifications)
        
        return Response({
            'message': f'{len(notifications)} notifications envoyées avec succès'
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'error': f'Erreur lors de l\'envoi: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def delete_notification(request, notification_id):
    """
    Vue pour supprimer une notification.
    
    DELETE /api/notifications/{id}/delete/
    """
    
    try:
        notification = Notification.objects.get(
            id=notification_id,
            destinataire=request.user
        )
        notification.delete()
        
        return Response({
            'message': 'Notification supprimée avec succès'
        }, status=status.HTTP_200_OK)
        
    except Notification.DoesNotExist:
        return Response({
            'error': 'Notification introuvable'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def test_notification(request):
    """
    Vue pour tester l'envoi d'une notification.
    
    POST /api/notifications/test/
    """
    
    # Créer une notification de test
    notification = Notification.objects.create(
        destinataire=request.user,
        titre='Notification de test',
        message='Ceci est une notification de test pour vérifier le système.',
        type_notification='SYSTEME',
        canal='IN_APP'
    )
    
    return Response({
        'message': 'Notification de test envoyée',
        'notification': NotificationSerializer(notification).data
    }, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def unread_count(request):
    """
    Vue pour obtenir le nombre de notifications non lues.
    
    GET /api/notifications/unread-count/
    """
    
    count = Notification.objects.filter(
        destinataire=request.user,
        statut='NOUVEAU'
    ).count()
    
    return Response({
        'unread_count': count
    }, status=status.HTTP_200_OK)

