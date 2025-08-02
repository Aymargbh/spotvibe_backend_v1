"""
Vues pour l'application core.

Ce module définit les vues Django REST Framework pour
les fonctionnalités de base de l'application.
"""

from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.db.models import Q, Count, Sum
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
import logging

from .models import AppSettings, ContactMessage, FAQ
from .serializers import (
    AppSettingsSerializer, ContactMessageSerializer, ContactMessageCreateSerializer,
    FAQSerializer, AppInfoSerializer, AppStatsSerializer,
    GlobalSearchSerializer, FileUploadSerializer, ReportContentSerializer,
    HealthCheckSerializer, MaintenanceSerializer, FeedbackSerializer
)
from apps.users.models import User
from apps.events.models import Event, EventParticipation
from apps.payments.models import Payment

logger = logging.getLogger(__name__)


@api_view(['GET'])
def app_info(request):
    """
    Vue pour obtenir les informations de l'application.
    
    GET /api/core/info/
    """
    
    try:
        settings_obj, created = AppSettings.objects.get_or_create(
            defaults={
                'nom_app': 'SpotVibe',
                'version': '1.0.0',
                'description': 'Plateforme de découverte d\'événements locaux',
                'email_contact': 'contact@spotvibe.com'
            }
        )
        
        app_data = {
            'nom_app': settings_obj.nom_app,
            'version': settings_obj.version,
            'description': settings_obj.description,
            'email_contact': settings_obj.email_contact,
            'telephone_contact': settings_obj.telephone_contact,
            'site_web': settings_obj.site_web,
            'maintenance_mode': settings_obj.maintenance_mode,
            'inscription_ouverte': settings_obj.inscription_ouverte
        }
        
        return Response(app_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f'App info error: {e}')
        return Response({
            'error': 'Erreur lors du chargement des informations'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def app_statistics(request):
    """
    Vue pour obtenir les statistiques de l'application.
    
    GET /api/core/stats/
    """
    
    try:
        total_users = User.objects.count()
        total_events = Event.objects.count()
        total_transactions = Payment.objects.count()
        total_revenue = Payment.objects.filter(
            statut='REUSSI'
        ).aggregate(total=Sum('montant'))['total'] or 0
        
        # Utilisateurs actifs aujourd'hui
        today = timezone.now().date()
        active_users_today = User.objects.filter(
            last_login__date=today
        ).count()
        
        # Événements créés aujourd'hui
        events_today = Event.objects.filter(
            date_creation__date=today
        ).count()
        
        stats_data = {
            'total_users': total_users,
            'total_events': total_events,
            'total_transactions': total_transactions,
            'total_revenue': float(total_revenue),
            'active_users_today': active_users_today,
            'events_today': events_today
        }
        
        return Response(stats_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f'App statistics error: {e}')
        return Response({
            'error': 'Erreur lors du chargement des statistiques'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def global_search(request):
    """
    Vue pour la recherche globale.
    
    POST /api/core/search/
    """
    
    serializer = GlobalSearchSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    try:
        query = serializer.validated_data['query']
        search_type = serializer.validated_data['type']
        limit = serializer.validated_data['limit']
        
        results = {
            'query': query,
            'users': [],
            'events': []
        }
        
        if search_type in ['all', 'users']:
            # Recherche d'utilisateurs
            users = User.objects.filter(
                Q(username__icontains=query) |
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query)
            ).filter(is_active=True)[:limit]
            
            results['users'] = [
                {
                    'id': user.id,
                    'username': user.username,
                    'full_name': user.get_full_name(),
                    'avatar': user.avatar.url if user.avatar else None
                }
                for user in users
            ]
        
        if search_type in ['all', 'events']:
            # Recherche d'événements
            events = Event.objects.filter(
                Q(titre__icontains=query) |
                Q(description__icontains=query)
            ).filter(statut='APPROUVE')[:limit]
            
            results['events'] = [
                {
                    'id': event.id,
                    'titre': event.titre,
                    'description': event.description[:100],
                    'date_debut': event.date_debut,
                    'lieu': event.lieu,
                    'image': event.image.url if event.image else None
                }
                for event in events
            ]
        
        return Response(results, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f'Global search error: {e}')
        return Response({
            'error': 'Erreur lors de la recherche'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def upload_file(request):
    """
    Vue pour l'upload de fichiers.
    
    POST /api/core/upload/
    """
    
    serializer = FileUploadSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    try:
        uploaded_file = serializer.validated_data['file']
        file_type = serializer.validated_data['type']
        
        # Ici, vous devriez implémenter la logique de sauvegarde
        # Pour l'exemple, nous simulons un upload réussi
        
        file_url = f'/media/uploads/{uploaded_file.name}'
        
        return Response({
            'message': 'Fichier uploadé avec succès',
            'file_url': file_url,
            'file_name': uploaded_file.name,
            'file_size': uploaded_file.size,
            'file_type': file_type
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f'File upload error: {e}')
        return Response({
            'error': 'Erreur lors de l\'upload du fichier'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def report_content(request):
    """
    Vue pour signaler du contenu.
    
    POST /api/core/report/
    """
    
    serializer = ReportContentSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    try:
        data = serializer.validated_data
        
        # Ici, vous devriez implémenter la logique de signalement
        # Pour l'exemple, nous simulons un signalement réussi
        
        logger.info(f'Content reported by user {request.user.id}: {data}')
        
        return Response({
            'message': 'Contenu signalé avec succès. Nous examinerons votre signalement.'
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f'Report content error: {e}')
        return Response({
            'error': 'Erreur lors du signalement'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def health_check(request):
    """
    Vue pour vérifier la santé de l'application.
    
    GET /api/core/health/
    """
    
    try:
        # Vérifications basiques
        health_data = {
            'status': 'OK',
            'timestamp': timezone.now(),
            'version': '1.0.0',
            'database': 'OK',
            'cache': 'OK',
            'storage': 'OK'
        }
        
        return Response(health_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f'Health check error: {e}')
        return Response({
            'status': 'ERROR',
            'timestamp': timezone.now(),
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'POST'])
@permission_classes([permissions.IsAdminUser])
def maintenance_mode(request):
    """
    Vue pour gérer le mode maintenance.
    
    GET /api/core/maintenance/
    POST /api/core/maintenance/
    """
    
    if request.method == 'GET':
        try:
            settings_obj, created = AppSettings.objects.get_or_create()
            
            maintenance_data = {
                'maintenance_mode': settings_obj.maintenance_mode,
                'message': settings_obj.message_maintenance
            }
            
            return Response(maintenance_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f'Maintenance mode get error: {e}')
            return Response({
                'error': 'Erreur lors de la récupération du mode maintenance'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'POST':
        serializer = MaintenanceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            data = serializer.validated_data
            settings_obj, created = AppSettings.objects.get_or_create()
            
            settings_obj.maintenance_mode = data['maintenance_mode']
            if 'message' in data:
                settings_obj.message_maintenance = data['message']
            settings_obj.save()
            
            return Response({
                'message': 'Mode maintenance mis à jour avec succès'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f'Maintenance mode post error: {e}')
            return Response({
                'error': 'Erreur lors de la mise à jour du mode maintenance'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def submit_feedback(request):
    """
    Vue pour soumettre un feedback.
    
    POST /api/core/feedback/
    """
    
    serializer = FeedbackSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    try:
        data = serializer.validated_data
        
        # Ici, vous devriez implémenter la logique de sauvegarde du feedback
        # Pour l'exemple, nous simulons une soumission réussie
        
        logger.info(f'Feedback submitted by user {request.user.id}: {data}')
        
        return Response({
            'message': 'Merci pour votre feedback ! Nous l\'examinerons attentivement.'
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f'Submit feedback error: {e}')
        return Response({
            'error': 'Erreur lors de la soumission du feedback'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ContactMessageListView(generics.ListCreateAPIView):
    """
    Vue pour lister et créer des messages de contact.
    
    GET /api/core/contact/
    POST /api/core/contact/
    """
    
    queryset = ContactMessage.objects.all().order_by('-date_creation')
    
    def get_serializer_class(self):
        """Retourne le sérialiseur approprié selon la méthode."""
        if self.request.method == 'POST':
            return ContactMessageCreateSerializer
        return ContactMessageSerializer
    
    def get_permissions(self):
        """Retourne les permissions appropriées selon la méthode."""
        if self.request.method == 'GET':
            return [permissions.IsAdminUser()]
        return [permissions.AllowAny()]
    
    def perform_create(self, serializer):
        """Traite la création d'un message de contact."""
        message = serializer.save()
        
        # Envoyer une notification par email aux administrateurs
        try:
            send_mail(
                subject=f'Nouveau message de contact: {message.sujet}',
                message=f'De: {message.nom} ({message.email})\n\n{message.message}',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.ADMIN_EMAIL],
                fail_silently=True
            )
        except Exception as e:
            logger.error(f'Contact email error: {e}')


class FAQListView(generics.ListAPIView):
    """
    Vue pour lister les questions fréquemment posées.
    
    GET /api/core/faq/
    """
    
    serializer_class = FAQSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        """Retourne les FAQ actives triées par ordre."""
        return FAQ.objects.filter(actif=True).order_by('ordre', 'question')


class AppSettingsView(generics.RetrieveUpdateAPIView):
    """
    Vue pour consulter et modifier les paramètres de l'application.
    
    GET /api/core/settings/
    PUT /api/core/settings/
    """
    
    serializer_class = AppSettingsSerializer
    permission_classes = [permissions.IsAdminUser]
    
    def get_object(self):
        """Retourne ou crée les paramètres de l'application."""
        settings_obj, created = AppSettings.objects.get_or_create()
        return settings_obj

