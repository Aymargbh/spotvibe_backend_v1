"""
Vues pour l'application payments.

Ce module définit les vues Django REST Framework pour
le système de paiement Mobile Money.
"""

from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Count, Sum, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
import logging
import json

from .models import Payment, MomoTransaction, Commission, Refund
from .serializers import (
    PaymentSerializer, PaymentCreateSerializer, MomoTransactionSerializer,
    CommissionSerializer, RefundSerializer, RefundCreateSerializer,
    PaymentStatsSerializer, WebhookDataSerializer, PaymentVerificationSerializer,
    PaymentCancelSerializer, PaymentRetrySerializer
)
from .services import PaymentService, MomoService

logger = logging.getLogger(__name__)


class PaymentPagination(PageNumberPagination):
    """Pagination personnalisée pour les paiements."""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class PaymentListView(generics.ListAPIView):
    """
    Vue pour lister les paiements de l'utilisateur.
    
    GET /api/payments/
    """
    
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = PaymentPagination
    
    def get_queryset(self):
        """Retourne les paiements de l'utilisateur avec filtres."""
        queryset = Payment.objects.filter(
            utilisateur=self.request.user
        ).order_by('-date_creation')
        
        # Filtres
        statut = self.request.query_params.get('statut')
        if statut:
            queryset = queryset.filter(statut=statut)
        
        type_paiement = self.request.query_params.get('type')
        if type_paiement:
            queryset = queryset.filter(type_paiement=type_paiement)
        
        methode = self.request.query_params.get('methode')
        if methode:
            queryset = queryset.filter(methode_paiement=methode)
        
        return queryset


class PaymentCreateView(generics.CreateAPIView):
    """
    Vue pour initier un paiement.
    
    POST /api/payments/initiate/
    """
    
    serializer_class = PaymentCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        """Initie un nouveau paiement."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            # Créer le paiement
            payment = serializer.save()
            
            # Initier la transaction Mobile Money
            payment_service = PaymentService()
            transaction_result = payment_service.initiate_payment(payment)
            
            if transaction_result['success']:
                return Response({
                    'message': 'Paiement initié avec succès',
                    'payment': PaymentSerializer(payment).data,
                    'transaction': transaction_result['data']
                }, status=status.HTTP_201_CREATED)
            else:
                # Marquer le paiement comme échoué
                payment.statut = 'ECHEC'
                payment.save()
                
                return Response({
                    'error': 'Échec de l\'initiation du paiement',
                    'details': transaction_result['error']
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f'Payment creation error: {e}')
            return Response({
                'error': 'Erreur lors de la création du paiement'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PaymentDetailView(generics.RetrieveAPIView):
    """
    Vue pour consulter les détails d'un paiement.
    
    GET /api/payments/{uuid}/
    """
    
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'uuid'
    
    def get_queryset(self):
        """Retourne les paiements de l'utilisateur."""
        return Payment.objects.filter(utilisateur=self.request.user)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def verify_payment(request):
    """
    Vue pour vérifier le statut d'un paiement.
    
    POST /api/payments/verify/
    """
    
    serializer = PaymentVerificationSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    payment_uuid = serializer.validated_data['payment_uuid']
    
    try:
        payment = Payment.objects.get(
            uuid=payment_uuid,
            utilisateur=request.user
        )
        
        # Vérifier le statut auprès du provider
        payment_service = PaymentService()
        verification_result = payment_service.verify_payment(payment)
        
        return Response({
            'payment': PaymentSerializer(payment).data,
            'verification': verification_result
        }, status=status.HTTP_200_OK)
        
    except Payment.DoesNotExist:
        return Response({
            'error': 'Paiement introuvable'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def cancel_payment(request):
    """
    Vue pour annuler un paiement en attente.
    
    POST /api/payments/cancel/
    """
    
    serializer = PaymentCancelSerializer(
        data=request.data,
        context={'request': request}
    )
    serializer.is_valid(raise_exception=True)
    
    payment_uuid = serializer.validated_data['payment_uuid']
    reason = serializer.validated_data.get('reason', '')
    
    try:
        payment = Payment.objects.get(
            uuid=payment_uuid,
            utilisateur=request.user,
            statut='EN_ATTENTE'
        )
        
        # Annuler le paiement
        payment.statut = 'ANNULE'
        payment.save()
        
        # Annuler la transaction Mobile Money si nécessaire
        payment_service = PaymentService()
        payment_service.cancel_payment(payment, reason)
        
        return Response({
            'message': 'Paiement annulé avec succès'
        }, status=status.HTTP_200_OK)
        
    except Payment.DoesNotExist:
        return Response({
            'error': 'Paiement introuvable ou ne peut pas être annulé'
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def retry_payment(request):
    """
    Vue pour relancer un paiement échoué.
    
    POST /api/payments/retry/
    """
    
    serializer = PaymentRetrySerializer(
        data=request.data,
        context={'request': request}
    )
    serializer.is_valid(raise_exception=True)
    
    payment_uuid = serializer.validated_data['payment_uuid']
    new_phone = serializer.validated_data.get('new_phone_number')
    
    try:
        payment = Payment.objects.get(
            uuid=payment_uuid,
            utilisateur=request.user,
            statut='ECHEC'
        )
        
        # Mettre à jour le numéro si fourni
        if new_phone:
            payment.telephone_paiement = new_phone
        
        # Remettre en attente
        payment.statut = 'EN_ATTENTE'
        payment.save()
        
        # Relancer la transaction
        payment_service = PaymentService()
        transaction_result = payment_service.initiate_payment(payment)
        
        if transaction_result['success']:
            return Response({
                'message': 'Paiement relancé avec succès',
                'payment': PaymentSerializer(payment).data
            }, status=status.HTTP_200_OK)
        else:
            payment.statut = 'ECHEC'
            payment.save()
            
            return Response({
                'error': 'Échec de la relance du paiement',
                'details': transaction_result['error']
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Payment.DoesNotExist:
        return Response({
            'error': 'Paiement introuvable ou ne peut pas être relancé'
        }, status=status.HTTP_400_BAD_REQUEST)


class RefundListView(generics.ListCreateAPIView):
    """
    Vue pour lister et créer des demandes de remboursement.
    
    GET /api/payments/refunds/
    POST /api/payments/refunds/
    """
    
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = PaymentPagination
    
    def get_serializer_class(self):
        """Retourne le sérialiseur approprié selon la méthode."""
        if self.request.method == 'POST':
            return RefundCreateSerializer
        return RefundSerializer
    
    def get_queryset(self):
        """Retourne les demandes de remboursement de l'utilisateur."""
        return Refund.objects.filter(
            demandeur=self.request.user
        ).select_related('payment').order_by('-date_demande')


class RefundDetailView(generics.RetrieveAPIView):
    """
    Vue pour consulter les détails d'une demande de remboursement.
    
    GET /api/payments/refunds/{id}/
    """
    
    serializer_class = RefundSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Retourne les demandes de remboursement de l'utilisateur."""
        return Refund.objects.filter(demandeur=self.request.user)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def payment_stats(request):
    """
    Vue pour obtenir les statistiques de paiements.
    
    GET /api/payments/stats/
    """
    
    user = request.user
    
    # Statistiques générales
    payments = Payment.objects.filter(utilisateur=user)
    
    total_payments = payments.count()
    successful_payments = payments.filter(statut='REUSSI').count()
    total_amount = payments.filter(statut='REUSSI').aggregate(
        total=Sum('montant')
    )['total'] or 0
    
    # Commissions
    total_commissions = Commission.objects.filter(
        payment__utilisateur=user,
        statut='VERSE'
    ).aggregate(total=Sum('montant_commission'))['total'] or 0
    
    # Paiements par méthode
    payments_by_method = dict(
        payments.values('methode_paiement')
        .annotate(count=Count('id'))
        .values_list('methode_paiement', 'count')
    )
    
    # Paiements par statut
    payments_by_status = dict(
        payments.values('statut')
        .annotate(count=Count('id'))
        .values_list('statut', 'count')
    )
    
    # Paiements récents
    recent_payments = payments.order_by('-date_creation')[:5]
    
    stats_data = {
        'total_payments': total_payments,
        'successful_payments': successful_payments,
        'total_amount': total_amount,
        'total_commissions': total_commissions,
        'payments_by_method': payments_by_method,
        'payments_by_status': payments_by_status,
        'recent_payments': PaymentSerializer(recent_payments, many=True).data
    }
    
    return Response(stats_data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def payment_methods(request):
    """
    Vue pour obtenir les méthodes de paiement disponibles.
    
    GET /api/payments/methods/
    """
    
    methods = [
        {
            'code': 'ORANGE_MONEY',
            'name': 'Orange Money',
            'description': 'Paiement via Orange Money',
            'icon': 'orange-money-icon.png',
            'available': True,
            'fees': '1%'
        },
        {
            'code': 'MTN_MONEY',
            'name': 'MTN Money',
            'description': 'Paiement via MTN Money',
            'icon': 'mtn-money-icon.png',
            'available': True,
            'fees': '1%'
        },
        {
            'code': 'MOOV_MONEY',
            'name': 'Moov Money',
            'description': 'Paiement via Moov Money',
            'icon': 'moov-money-icon.png',
            'available': True,
            'fees': '1%'
        }
    ]
    
    return Response(methods, status=status.HTTP_200_OK)


# Webhooks pour les providers Mobile Money

@csrf_exempt
@api_view(['POST'])
@permission_classes([])
def orange_money_webhook(request):
    """
    Webhook pour Orange Money.
    
    POST /api/payments/webhooks/orange/
    """
    
    try:
        data = request.data
        logger.info(f'Orange Money webhook received: {data}')
        
        # Valider les données
        serializer = WebhookDataSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        
        # Traiter le webhook
        momo_service = MomoService()
        result = momo_service.process_orange_webhook(serializer.validated_data)
        
        if result['success']:
            return Response({'status': 'OK'}, status=status.HTTP_200_OK)
        else:
            return Response(
                {'error': result['error']},
                status=status.HTTP_400_BAD_REQUEST
            )
            
    except Exception as e:
        logger.error(f'Orange Money webhook error: {e}')
        return Response(
            {'error': 'Webhook processing failed'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@csrf_exempt
@api_view(['POST'])
@permission_classes([])
def mtn_money_webhook(request):
    """
    Webhook pour MTN Money.
    
    POST /api/payments/webhooks/mtn/
    """
    
    try:
        data = request.data
        logger.info(f'MTN Money webhook received: {data}')
        
        # Valider les données
        serializer = WebhookDataSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        
        # Traiter le webhook
        momo_service = MomoService()
        result = momo_service.process_mtn_webhook(serializer.validated_data)
        
        if result['success']:
            return Response({'status': 'OK'}, status=status.HTTP_200_OK)
        else:
            return Response(
                {'error': result['error']},
                status=status.HTTP_400_BAD_REQUEST
            )
            
    except Exception as e:
        logger.error(f'MTN Money webhook error: {e}')
        return Response(
            {'error': 'Webhook processing failed'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@csrf_exempt
@api_view(['POST'])
@permission_classes([])
def moov_money_webhook(request):
    """
    Webhook pour Moov Money.
    
    POST /api/payments/webhooks/moov/
    """
    
    try:
        data = request.data
        logger.info(f'Moov Money webhook received: {data}')
        
        # Valider les données
        serializer = WebhookDataSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        
        # Traiter le webhook
        momo_service = MomoService()
        result = momo_service.process_moov_webhook(serializer.validated_data)
        
        if result['success']:
            return Response({'status': 'OK'}, status=status.HTTP_200_OK)
        else:
            return Response(
                {'error': result['error']},
                status=status.HTTP_400_BAD_REQUEST
            )
            
    except Exception as e:
        logger.error(f'Moov Money webhook error: {e}')
        return Response(
            {'error': 'Webhook processing failed'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class MomoTransactionListView(generics.ListAPIView):
    """
    Vue pour lister les transactions Mobile Money.
    
    GET /api/payments/transactions/
    """
    
    serializer_class = MomoTransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = PaymentPagination
    
    def get_queryset(self):
        """Retourne les transactions de l'utilisateur."""
        return MomoTransaction.objects.filter(
            payment__utilisateur=self.request.user
        ).select_related('payment').order_by('-date_creation')


class CommissionListView(generics.ListAPIView):
    """
    Vue pour lister les commissions.
    
    GET /api/payments/commissions/
    """
    
    serializer_class = CommissionSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = PaymentPagination
    
    def get_queryset(self):
        """Retourne les commissions selon les permissions."""
        if self.request.user.is_staff:
            return Commission.objects.all().select_related('payment').order_by('-date_creation')
        else:
            return Commission.objects.filter(
                payment__utilisateur=self.request.user
            ).select_related('payment').order_by('-date_creation')


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_payment_summary(request):
    """
    Vue pour obtenir un résumé des paiements de l'utilisateur.
    
    GET /api/payments/summary/
    """
    
    user = request.user
    
    # Paiements du mois en cours
    current_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    monthly_payments = Payment.objects.filter(
        utilisateur=user,
        date_creation__gte=current_month,
        statut='REUSSI'
    )
    
    summary = {
        'monthly_total': monthly_payments.aggregate(
            total=Sum('montant')
        )['total'] or 0,
        'monthly_count': monthly_payments.count(),
        'pending_payments': Payment.objects.filter(
            utilisateur=user,
            statut='EN_ATTENTE'
        ).count(),
        'failed_payments': Payment.objects.filter(
            utilisateur=user,
            statut='ECHEC'
        ).count(),
        'pending_refunds': Refund.objects.filter(
            demandeur=user,
            statut='EN_ATTENTE'
        ).count()
    }
    
    return Response(summary, status=status.HTTP_200_OK)

