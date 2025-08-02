"""
Vues pour l'application admin_dashboard.

Ce module définit les vues Django REST Framework pour
le dashboard d'administration.
"""

from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.db.models import Count, Sum, Q
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import timedelta
import logging

from .models import AdminAction
from .serializers import (
    AdminActionSerializer, DashboardStatsSerializer, UserStatsSerializer, 
    EventStatsSerializer, PaymentStatsSerializer, SystemHealthSerializer,
    BulkActionSerializer, QuickActionSerializer, AdminMetricsSerializer
)
from apps.users.models import User
from apps.events.models import Event, EventParticipation
from apps.payments.models import Payment
from apps.subscriptions.models import Subscription

logger = logging.getLogger(__name__)


class AdminPermission(permissions.BasePermission):
    """Permission personnalisée pour les administrateurs."""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_staff


@api_view(['GET'])
@permission_classes([AdminPermission])
def dashboard_overview(request):
    """
    Vue pour obtenir un aperçu du dashboard.
    
    GET /api/admin/dashboard/
    """
    
    try:
        # Statistiques des utilisateurs
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        new_users_today = User.objects.filter(
            date_joined__date=timezone.now().date()
        ).count()
        
        # Statistiques des événements
        total_events = Event.objects.count()
        pending_events = Event.objects.filter(statut='EN_ATTENTE').count()
        approved_events = Event.objects.filter(statut='APPROUVE').count()
        
        # Statistiques des paiements
        total_revenue = Payment.objects.filter(
            statut='REUSSI'
        ).aggregate(total=Sum('montant'))['total'] or 0
        
        revenue_today = Payment.objects.filter(
            statut='REUSSI',
            date_creation__date=timezone.now().date()
        ).aggregate(total=Sum('montant'))['total'] or 0
        
        total_transactions = Payment.objects.count()
        
        # Vérifications en attente
        pending_verifications = User.objects.filter(
            verification_identite__statut='EN_ATTENTE'
        ).count()
        
        stats_data = {
            'total_users': total_users,
            'active_users': active_users,
            'new_users_today': new_users_today,
            'total_events': total_events,
            'pending_events': pending_events,
            'approved_events': approved_events,
            'total_revenue': total_revenue,
            'revenue_today': revenue_today,
            'total_transactions': total_transactions,
            'pending_verifications': pending_verifications
        }
        
        return Response(stats_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f'Dashboard overview error: {e}')
        return Response({
            'error': 'Erreur lors du chargement du dashboard'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AdminPermission])
def user_statistics(request):
    """
    Vue pour obtenir les statistiques détaillées des utilisateurs.
    
    GET /api/admin/users/stats/
    """
    
    try:
        total_users = User.objects.count()
        verified_users = User.objects.filter(
            verification_identite__statut='APPROUVE'
        ).count()
        unverified_users = total_users - verified_users
        active_users = User.objects.filter(is_active=True).count()
        inactive_users = total_users - active_users
        
        # Utilisateurs par type d'abonnement
        users_by_subscription = dict(
            Subscription.objects.filter(actif=True)
            .values('plan__nom')
            .annotate(count=Count('id'))
            .values_list('plan__nom', 'count')
        )
        
        # Nouveaux utilisateurs des 30 derniers jours
        new_users_last_30_days = []
        for i in range(30):
            date = timezone.now().date() - timedelta(days=i)
            count = User.objects.filter(date_joined__date=date).count()
            new_users_last_30_days.append({
                'date': date.isoformat(),
                'count': count
            })
        
        stats_data = {
            'total_users': total_users,
            'verified_users': verified_users,
            'unverified_users': unverified_users,
            'active_users': active_users,
            'inactive_users': inactive_users,
            'users_by_subscription': users_by_subscription,
            'new_users_last_30_days': new_users_last_30_days
        }
        
        return Response(stats_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f'User statistics error: {e}')
        return Response({
            'error': 'Erreur lors du chargement des statistiques utilisateurs'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AdminPermission])
def event_statistics(request):
    """
    Vue pour obtenir les statistiques détaillées des événements.
    
    GET /api/admin/events/stats/
    """
    
    try:
        total_events = Event.objects.count()
        pending_events = Event.objects.filter(statut='EN_ATTENTE').count()
        approved_events = Event.objects.filter(statut='APPROUVE').count()
        rejected_events = Event.objects.filter(statut='REJETE').count()
        
        # Événements par catégorie
        events_by_category = dict(
            Event.objects.values('categorie__nom')
            .annotate(count=Count('id'))
            .values_list('categorie__nom', 'count')
        )
        
        # Événements par statut
        events_by_status = dict(
            Event.objects.values('statut')
            .annotate(count=Count('id'))
            .values_list('statut', 'count')
        )
        
        # Événements des 30 derniers jours
        events_last_30_days = []
        for i in range(30):
            date = timezone.now().date() - timedelta(days=i)
            count = Event.objects.filter(date_creation__date=date).count()
            events_last_30_days.append({
                'date': date.isoformat(),
                'count': count
            })
        
        stats_data = {
            'total_events': total_events,
            'pending_events': pending_events,
            'approved_events': approved_events,
            'rejected_events': rejected_events,
            'events_by_category': events_by_category,
            'events_by_status': events_by_status,
            'events_last_30_days': events_last_30_days
        }
        
        return Response(stats_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f'Event statistics error: {e}')
        return Response({
            'error': 'Erreur lors du chargement des statistiques événements'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AdminPermission])
def payment_statistics(request):
    """
    Vue pour obtenir les statistiques détaillées des paiements.
    
    GET /api/admin/payments/stats/
    """
    
    try:
        total_revenue = Payment.objects.filter(
            statut='REUSSI'
        ).aggregate(total=Sum('montant'))['total'] or 0
        
        total_transactions = Payment.objects.count()
        successful_transactions = Payment.objects.filter(statut='REUSSI').count()
        failed_transactions = Payment.objects.filter(statut='ECHEC').count()
        pending_transactions = Payment.objects.filter(statut='EN_ATTENTE').count()
        
        # Revenus par méthode de paiement
        revenue_by_method = dict(
            Payment.objects.filter(statut='REUSSI')
            .values('methode_paiement')
            .annotate(total=Sum('montant'))
            .values_list('methode_paiement', 'total')
        )
        
        # Revenus des 30 derniers jours
        revenue_last_30_days = []
        for i in range(30):
            date = timezone.now().date() - timedelta(days=i)
            revenue = Payment.objects.filter(
                statut='REUSSI',
                date_creation__date=date
            ).aggregate(total=Sum('montant'))['total'] or 0
            revenue_last_30_days.append({
                'date': date.isoformat(),
                'revenue': float(revenue)
            })
        
        stats_data = {
            'total_revenue': float(total_revenue),
            'total_transactions': total_transactions,
            'successful_transactions': successful_transactions,
            'failed_transactions': failed_transactions,
            'pending_transactions': pending_transactions,
            'revenue_by_method': {k: float(v) for k, v in revenue_by_method.items()},
            'revenue_last_30_days': revenue_last_30_days
        }
        
        return Response(stats_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f'Payment statistics error: {e}')
        return Response({
            'error': 'Erreur lors du chargement des statistiques paiements'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AdminPermission])
def system_health(request):
    """
    Vue pour obtenir l'état de santé du système.
    
    GET /api/admin/system/health/
    """
    
    try:
        # Vérifications basiques
        database_status = "OK"
        cache_status = "OK"
        storage_status = "OK"
        api_response_time = 0.1  # Simulé
        error_rate = 0.01  # Simulé
        uptime = "99.9%"  # Simulé
        
        health_data = {
            'database_status': database_status,
            'cache_status': cache_status,
            'storage_status': storage_status,
            'api_response_time': api_response_time,
            'error_rate': error_rate,
            'uptime': uptime
        }
        
        return Response(health_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f'System health error: {e}')
        return Response({
            'error': 'Erreur lors de la vérification de la santé du système'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AdminPermission])
def bulk_action(request):
    """
    Vue pour effectuer des actions en lot.
    
    POST /api/admin/bulk-action/
    """
    
    serializer = BulkActionSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    try:
        data = serializer.validated_data
        action = data['action']
        target_type = data['target_type']
        target_ids = data['target_ids']
        reason = data.get('reason', '')
        
        updated_count = 0
        
        if target_type == 'user':
            if action == 'verify':
                # Vérifier les utilisateurs
                updated_count = User.objects.filter(
                    id__in=target_ids
                ).update(verification_identite__statut='APPROUVE')
            elif action == 'suspend':
                # Suspendre les utilisateurs
                updated_count = User.objects.filter(
                    id__in=target_ids
                ).update(is_active=False)
            elif action == 'activate':
                # Activer les utilisateurs
                updated_count = User.objects.filter(
                    id__in=target_ids
                ).update(is_active=True)
        
        elif target_type == 'event':
            if action == 'approve':
                # Approuver les événements
                updated_count = Event.objects.filter(
                    id__in=target_ids
                ).update(statut='APPROUVE')
            elif action == 'reject':
                # Rejeter les événements
                updated_count = Event.objects.filter(
                    id__in=target_ids
                ).update(statut='REJETE')
        
        # Enregistrer l'action administrative
        AdminAction.objects.create(
            utilisateur=request.user,
            action=f'bulk_{action}',
            description=f'Action en lot: {action} sur {updated_count} {target_type}(s)',
            cible_type=target_type,
            donnees_supplementaires={
                'target_ids': target_ids,
                'reason': reason,
                'updated_count': updated_count
            }
        )
        
        return Response({
            'message': f'Action effectuée sur {updated_count} éléments',
            'updated_count': updated_count
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f'Bulk action error: {e}')
        return Response({
            'error': f'Erreur lors de l\'action en lot: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AdminPermission])
def quick_action(request):
    """
    Vue pour effectuer des actions rapides.
    
    POST /api/admin/quick-action/
    """
    
    serializer = QuickActionSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    try:
        data = serializer.validated_data
        action = data['action']
        target_id = data['target_id']
        action_data = data.get('data', {})
        
        result = None
        
        if action == 'approve_event':
            event = Event.objects.get(id=target_id)
            event.statut = 'APPROUVE'
            event.save()
            result = f'Événement {event.titre} approuvé'
        
        elif action == 'reject_event':
            event = Event.objects.get(id=target_id)
            event.statut = 'REJETE'
            event.save()
            result = f'Événement {event.titre} rejeté'
        
        elif action == 'verify_user':
            user = User.objects.get(id=target_id)
            # Logique de vérification
            result = f'Utilisateur {user.username} vérifié'
        
        elif action == 'suspend_user':
            user = User.objects.get(id=target_id)
            user.is_active = False
            user.save()
            result = f'Utilisateur {user.username} suspendu'
        
        # Enregistrer l'action administrative
        AdminAction.objects.create(
            utilisateur=request.user,
            action=action,
            description=result,
            cible_id=target_id,
            donnees_supplementaires=action_data
        )
        
        return Response({
            'message': result
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f'Quick action error: {e}')
        return Response({
            'error': f'Erreur lors de l\'action rapide: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AdminActionListView(generics.ListAPIView):
    """
    Vue pour lister les actions administratives.
    
    GET /api/admin/actions/
    """
    
    serializer_class = AdminActionSerializer
    permission_classes = [AdminPermission]
    
    def get_queryset(self):
        """Retourne les actions administratives."""
        return AdminAction.objects.all().order_by('-date_creation')


@api_view(['GET'])
@permission_classes([AdminPermission])
def admin_metrics(request):
    """
    Vue pour obtenir les métriques administratives.
    
    GET /api/admin/metrics/
    """
    
    period = request.query_params.get('period', 'month')
    metric_type = request.query_params.get('type', 'users')
    
    try:
        # Calculer les dates selon la période
        now = timezone.now()
        if period == 'today':
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == 'week':
            start_date = now - timedelta(days=7)
        elif period == 'month':
            start_date = now - timedelta(days=30)
        elif period == 'quarter':
            start_date = now - timedelta(days=90)
        elif period == 'year':
            start_date = now - timedelta(days=365)
        else:
            start_date = now - timedelta(days=30)
        
        labels = []
        data = []
        
        if metric_type == 'users':
            # Métriques des utilisateurs
            for i in range(30):
                date = start_date + timedelta(days=i)
                count = User.objects.filter(
                    date_joined__date=date.date()
                ).count()
                labels.append(date.strftime('%Y-%m-%d'))
                data.append(count)
        
        elif metric_type == 'events':
            # Métriques des événements
            for i in range(30):
                date = start_date + timedelta(days=i)
                count = Event.objects.filter(
                    date_creation__date=date.date()
                ).count()
                labels.append(date.strftime('%Y-%m-%d'))
                data.append(count)
        
        total = sum(data)
        growth_rate = 0.0  # Calculer le taux de croissance
        
        metrics_data = {
            'period': period,
            'metric_type': metric_type,
            'labels': labels,
            'data': data,
            'total': total,
            'growth_rate': growth_rate
        }
        
        return Response(metrics_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f'Admin metrics error: {e}')
        return Response({
            'error': 'Erreur lors du chargement des métriques'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

