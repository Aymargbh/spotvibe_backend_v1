"""
Vues pour l'application subscriptions.

Ce module définit les vues Django REST Framework pour
le système d'abonnements.
"""

from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import timedelta
import logging

from .models import SubscriptionPlan, Subscription, SubscriptionHistory
from .serializers import (
    SubscriptionPlanSerializer, SubscriptionSerializer,
    SubscriptionCreateSerializer, SubscriptionUpdateSerializer,
    SubscriptionHistorySerializer, SubscriptionStatsSerializer,
    SubscriptionRenewalSerializer, SubscriptionCancelSerializer,
    SubscriptionUpgradeSerializer, SubscriptionUsageSerializer,
    SubscriptionBenefitsSerializer, SubscriptionComparisonSerializer,
    SubscriptionPaymentSerializer
)
from .services import SubscriptionService

logger = logging.getLogger(__name__)


class SubscriptionPagination(PageNumberPagination):
    """Pagination personnalisée pour les abonnements."""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class SubscriptionPlanListView(generics.ListAPIView):
    """
    Vue pour lister les plans d'abonnement disponibles.
    
    GET /api/subscriptions/plans/
    """
    
    serializer_class = SubscriptionPlanSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        """Retourne les plans actifs."""
        return SubscriptionPlan.objects.filter(actif=True).order_by('prix')


class SubscriptionPlanDetailView(generics.RetrieveAPIView):
    """
    Vue pour consulter les détails d'un plan d'abonnement.
    
    GET /api/subscriptions/plans/{id}/
    """
    
    serializer_class = SubscriptionPlanSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        """Retourne les plans actifs."""
        return SubscriptionPlan.objects.filter(actif=True)


class SubscriptionListView(generics.ListCreateAPIView):
    """
    Vue pour lister et créer des abonnements.
    
    GET /api/subscriptions/
    POST /api/subscriptions/
    """
    
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = SubscriptionPagination
    
    def get_serializer_class(self):
        """Retourne le sérialiseur approprié selon la méthode."""
        if self.request.method == 'POST':
            return SubscriptionCreateSerializer
        return SubscriptionSerializer
    
    def get_queryset(self):
        """Retourne les abonnements de l'utilisateur."""
        return Subscription.objects.filter(
            utilisateur=self.request.user
        ).select_related('plan').order_by('-date_creation')


class SubscriptionDetailView(generics.RetrieveUpdateAPIView):
    """
    Vue pour consulter et modifier un abonnement.
    
    GET /api/subscriptions/{id}/
    PUT /api/subscriptions/{id}/
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        """Retourne le sérialiseur approprié selon la méthode."""
        if self.request.method in ['PUT', 'PATCH']:
            return SubscriptionUpdateSerializer
        return SubscriptionSerializer
    
    def get_queryset(self):
        """Retourne les abonnements de l'utilisateur."""
        return Subscription.objects.filter(
            utilisateur=self.request.user
        ).select_related('plan')


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def current_subscription(request):
    """
    Vue pour obtenir l'abonnement actuel de l'utilisateur.
    
    GET /api/subscriptions/current/
    """
    
    try:
        subscription = Subscription.objects.get(
            utilisateur=request.user,
            statut='ACTIF'
        )
        
        serializer = SubscriptionSerializer(subscription)
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    except Subscription.DoesNotExist:
        return Response({
            'message': 'Aucun abonnement actif',
            'has_subscription': False
        }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def renew_subscription(request):
    """
    Vue pour renouveler un abonnement.
    
    POST /api/subscriptions/renew/
    """
    
    serializer = SubscriptionRenewalSerializer(
        data=request.data,
        context={'request': request}
    )
    serializer.is_valid(raise_exception=True)
    
    try:
        subscription_service = SubscriptionService()
        result = subscription_service.renew_subscription(
            serializer.validated_data['subscription'],
            serializer.validated_data['new_plan']
        )
        
        if result['success']:
            return Response({
                'message': 'Abonnement renouvelé avec succès',
                'subscription': SubscriptionSerializer(result['subscription']).data
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': result['error']
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f'Subscription renewal error: {e}')
        return Response({
            'error': 'Erreur lors du renouvellement'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def cancel_subscription(request):
    """
    Vue pour annuler un abonnement.
    
    POST /api/subscriptions/cancel/
    """
    
    serializer = SubscriptionCancelSerializer(
        data=request.data,
        context={'request': request}
    )
    serializer.is_valid(raise_exception=True)
    
    try:
        subscription_id = serializer.validated_data['subscription_id']
        reason = serializer.validated_data.get('reason', '')
        cancel_immediately = serializer.validated_data.get('cancel_immediately', False)
        
        subscription = Subscription.objects.get(
            id=subscription_id,
            utilisateur=request.user
        )
        
        subscription_service = SubscriptionService()
        result = subscription_service.cancel_subscription(
            subscription, reason, cancel_immediately
        )
        
        if result['success']:
            return Response({
                'message': 'Abonnement annulé avec succès'
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': result['error']
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f'Subscription cancellation error: {e}')
        return Response({
            'error': 'Erreur lors de l\'annulation'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def upgrade_subscription(request):
    """
    Vue pour mettre à niveau un abonnement.
    
    POST /api/subscriptions/upgrade/
    """
    
    serializer = SubscriptionUpgradeSerializer(
        data=request.data,
        context={'request': request}
    )
    serializer.is_valid(raise_exception=True)
    
    try:
        subscription_service = SubscriptionService()
        result = subscription_service.upgrade_subscription(
            serializer.validated_data['subscription'],
            serializer.validated_data['new_plan']
        )
        
        if result['success']:
            return Response({
                'message': 'Abonnement mis à niveau avec succès',
                'subscription': SubscriptionSerializer(result['subscription']).data,
                'payment_required': result.get('payment_required', False),
                'amount_due': result.get('amount_due', 0)
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': result['error']
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f'Subscription upgrade error: {e}')
        return Response({
            'error': 'Erreur lors de la mise à niveau'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def subscription_usage(request):
    """
    Vue pour obtenir l'utilisation de l'abonnement.
    
    GET /api/subscriptions/usage/
    """
    
    try:
        subscription = Subscription.objects.get(
            utilisateur=request.user,
            statut='ACTIF'
        )
        
        subscription_service = SubscriptionService()
        usage_data = subscription_service.get_usage_stats(subscription)
        
        return Response(usage_data, status=status.HTTP_200_OK)
        
    except Subscription.DoesNotExist:
        return Response({
            'error': 'Aucun abonnement actif'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def subscription_benefits(request):
    """
    Vue pour obtenir les avantages de l'abonnement.
    
    GET /api/subscriptions/benefits/
    """
    
    try:
        subscription = Subscription.objects.get(
            utilisateur=request.user,
            statut='ACTIF'
        )
        
        benefits_data = {
            'plan_name': subscription.plan.nom,
            'features': subscription.plan.features.get('features', []) if subscription.plan.features else [],
            'limits': {
                'events': subscription.plan.limite_evenements,
                'participants': subscription.plan.limite_participants,
                'photos': subscription.plan.limite_photos
            },
            'premium_features': [
                'Support prioritaire' if subscription.plan.support_prioritaire else None,
                'Analytics avancés' if subscription.plan.analytics_avances else None,
                'Promotion premium' if subscription.plan.promotion_premium else None,
                'Badge vérifié' if subscription.plan.badge_verifie else None
            ],
            'support_level': 'Prioritaire' if subscription.plan.support_prioritaire else 'Standard'
        }
        
        # Filtrer les fonctionnalités None
        benefits_data['premium_features'] = [
            f for f in benefits_data['premium_features'] if f is not None
        ]
        
        return Response(benefits_data, status=status.HTTP_200_OK)
        
    except Subscription.DoesNotExist:
        return Response({
            'plan_name': 'Gratuit',
            'features': ['Création d\'événements de base', 'Participation aux événements'],
            'limits': {
                'events': 2,
                'participants': 50,
                'photos': 10
            },
            'premium_features': [],
            'support_level': 'Communautaire'
        }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def plans_comparison(request):
    """
    Vue pour comparer les plans d'abonnement.
    
    GET /api/subscriptions/compare/
    """
    
    plans = SubscriptionPlan.objects.filter(actif=True).order_by('prix')
    
    current_plan = None
    if request.user.is_authenticated:
        try:
            current_subscription = Subscription.objects.get(
                utilisateur=request.user,
                statut='ACTIF'
            )
            current_plan = current_subscription.plan
        except Subscription.DoesNotExist:
            pass
    
    recommendations = []
    if current_plan:
        if current_plan.nom.lower() == 'standard':
            recommendations.append('Passez au Premium pour plus de participants')
        elif current_plan.nom.lower() == 'premium':
            recommendations.append('Le Gold offre un support prioritaire')
    else:
        recommendations.append('Commencez avec le plan Standard')
    
    comparison_data = {
        'plans': SubscriptionPlanSerializer(plans, many=True).data,
        'current_plan': SubscriptionPlanSerializer(current_plan).data if current_plan else None,
        'recommendations': recommendations
    }
    
    return Response(comparison_data, status=status.HTTP_200_OK)


class SubscriptionHistoryListView(generics.ListAPIView):
    """
    Vue pour lister l'historique des abonnements.
    
    GET /api/subscriptions/history/
    """
    
    serializer_class = SubscriptionHistorySerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = SubscriptionPagination
    
    def get_queryset(self):
        """Retourne l'historique de l'utilisateur."""
        return SubscriptionHistory.objects.filter(
            utilisateur=self.request.user
        ).select_related('plan').order_by('-date_action')


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def subscription_stats(request):
    """
    Vue pour obtenir les statistiques d'abonnements.
    
    GET /api/subscriptions/stats/
    """
    
    if not request.user.is_staff:
        return Response({
            'error': 'Permission refusée'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Statistiques générales
    total_subscriptions = Subscription.objects.count()
    active_subscriptions = Subscription.objects.filter(statut='ACTIF').count()
    expired_subscriptions = Subscription.objects.filter(statut='EXPIRE').count()
    
    # Revenus
    current_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    revenue_this_month = SubscriptionHistory.objects.filter(
        action='ACTIVATION',
        date_action__gte=current_month
    ).aggregate(total=Sum('montant_paye'))['total'] or 0
    
    revenue_total = SubscriptionHistory.objects.filter(
        action='ACTIVATION'
    ).aggregate(total=Sum('montant_paye'))['total'] or 0
    
    # Abonnements par plan
    subscriptions_by_plan = dict(
        Subscription.objects.filter(statut='ACTIF')
        .values('plan__nom')
        .annotate(count=Count('id'))
        .values_list('plan__nom', 'count')
    )
    
    # Abonnements récents
    recent_subscriptions = Subscription.objects.select_related('plan', 'utilisateur').order_by('-date_creation')[:5]
    
    stats_data = {
        'total_subscriptions': total_subscriptions,
        'active_subscriptions': active_subscriptions,
        'expired_subscriptions': expired_subscriptions,
        'revenue_this_month': revenue_this_month,
        'revenue_total': revenue_total,
        'subscriptions_by_plan': subscriptions_by_plan,
        'recent_subscriptions': SubscriptionSerializer(recent_subscriptions, many=True).data
    }
    
    return Response(stats_data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def pay_subscription(request):
    """
    Vue pour payer un abonnement.
    
    POST /api/subscriptions/pay/
    """
    
    serializer = SubscriptionPaymentSerializer(
        data=request.data,
        context={'request': request}
    )
    serializer.is_valid(raise_exception=True)
    
    try:
        subscription_id = serializer.validated_data['subscription_id']
        payment_method = serializer.validated_data['payment_method']
        phone_number = serializer.validated_data['phone_number']
        
        subscription = Subscription.objects.get(
            id=subscription_id,
            utilisateur=request.user,
            statut='EN_ATTENTE'
        )
        
        # Créer le paiement via l'API payments
        from apps.payments.serializers import PaymentCreateSerializer
        
        payment_data = {
            'type_paiement': 'ABONNEMENT',
            'montant': subscription.plan.prix,
            'methode_paiement': payment_method,
            'telephone_paiement': phone_number,
            'description': f'Abonnement {subscription.plan.nom}',
            'subscription_id': subscription.id
        }
        
        payment_serializer = PaymentCreateSerializer(
            data=payment_data,
            context={'request': request}
        )
        payment_serializer.is_valid(raise_exception=True)
        payment = payment_serializer.save()
        
        # Associer le paiement à l'abonnement
        subscription.reference_paiement = payment.uuid
        subscription.save()
        
        return Response({
            'message': 'Paiement initié avec succès',
            'payment_uuid': payment.uuid,
            'subscription': SubscriptionSerializer(subscription).data
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f'Subscription payment error: {e}')
        return Response({
            'error': 'Erreur lors de l\'initiation du paiement'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([])
def activate_subscription_webhook(request):
    """
    Webhook pour activer un abonnement après paiement réussi.
    
    POST /api/subscriptions/activate-webhook/
    """
    
    try:
        payment_uuid = request.data.get('payment_uuid')
        if not payment_uuid:
            return Response({
                'error': 'payment_uuid requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Trouver l'abonnement
        subscription = Subscription.objects.filter(
            reference_paiement=payment_uuid,
            statut='EN_ATTENTE'
        ).first()
        
        if not subscription:
            return Response({
                'error': 'Abonnement introuvable'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Activer l'abonnement
        subscription_service = SubscriptionService()
        result = subscription_service.activate_subscription(subscription)
        
        if result['success']:
            return Response({
                'message': 'Abonnement activé avec succès'
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': result['error']
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f'Subscription activation webhook error: {e}')
        return Response({
            'error': 'Erreur lors de l\'activation'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

