"""
Sérialiseurs pour l'application payments.

Ce module définit les sérialiseurs Django REST Framework pour
le système de paiement Mobile Money.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from decimal import Decimal
from .models import Payment, MomoTransaction, Commission, Refund
from apps.users.serializers import UserPublicSerializer
from apps.events.models import EventTicket
from apps.subscriptions.models import Subscription

User = get_user_model()


class PaymentSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour les paiements.
    """
    
    utilisateur = UserPublicSerializer(read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id', 'uuid', 'utilisateur', 'type_paiement', 'montant',
            'devise', 'statut', 'methode_paiement', 'telephone_paiement',
            'reference_externe', 'description', 'date_creation',
            'date_completion', 'donnees_supplementaires'
        ]
        read_only_fields = [
            'id', 'uuid', 'utilisateur', 'statut', 'reference_externe',
            'date_creation', 'date_completion'
        ]


class PaymentCreateSerializer(serializers.Serializer):
    """
    Sérialiseur pour créer un paiement.
    """
    
    type_paiement = serializers.ChoiceField(
        choices=['BILLET', 'ABONNEMENT', 'COMMISSION']
    )
    montant = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=100)
    methode_paiement = serializers.ChoiceField(
        choices=['MTN_MONEY', 'MOOV_MONEY']
    )
    telephone_paiement = serializers.CharField(max_length=20)
    description = serializers.CharField(max_length=500, required=False)
    
    # Champs conditionnels
    ticket_id = serializers.IntegerField(required=False)
    subscription_id = serializers.IntegerField(required=False)
    
    def validate_telephone_paiement(self, value):
        """Valide le numéro de téléphone."""
        if not value.startswith('+229'):
            raise serializers.ValidationError(
                "Le numéro doit commencer par +229"
            )
        if len(value) != 15:
            raise serializers.ValidationError(
                "Format invalide. Utilisez +229XXXXXXXX"
            )
        return value
    
    def validate(self, attrs):
        """Validation globale."""
        type_paiement = attrs['type_paiement']
        
        if type_paiement == 'BILLET':
            if 'ticket_id' not in attrs:
                raise serializers.ValidationError(
                    "ticket_id requis pour un paiement de billet"
                )
            
            # Vérifier que le billet existe et appartient à l'utilisateur
            try:
                ticket = EventTicket.objects.get(
                    id=attrs['ticket_id'],
                    utilisateur=self.context['request'].user,
                    statut='EN_ATTENTE'
                )
                attrs['ticket'] = ticket
                
                # Vérifier le montant
                expected_amount = ticket.get_total_price()
                if attrs['montant'] != expected_amount:
                    raise serializers.ValidationError(
                        f"Montant incorrect. Attendu: {expected_amount}"
                    )
                    
            except EventTicket.DoesNotExist:
                raise serializers.ValidationError(
                    "Billet introuvable ou déjà payé"
                )
        
        elif type_paiement == 'ABONNEMENT':
            if 'subscription_id' not in attrs:
                raise serializers.ValidationError(
                    "subscription_id requis pour un paiement d'abonnement"
                )
            
            # Vérifier que l'abonnement existe
            try:
                subscription = Subscription.objects.get(
                    id=attrs['subscription_id'],
                    utilisateur=self.context['request'].user,
                    statut='EN_ATTENTE'
                )
                attrs['subscription'] = subscription
                
                # Vérifier le montant
                expected_amount = subscription.plan.prix
                if attrs['montant'] != expected_amount:
                    raise serializers.ValidationError(
                        f"Montant incorrect. Attendu: {expected_amount}"
                    )
                    
            except Subscription.DoesNotExist:
                raise serializers.ValidationError(
                    "Abonnement introuvable ou déjà payé"
                )
        
        return attrs
    
    def create(self, validated_data):
        """Crée un paiement."""
        user = self.context['request'].user
        
        # Extraire les objets liés
        ticket = validated_data.pop('ticket', None)
        subscription = validated_data.pop('subscription', None)
        
        # Créer le paiement
        payment = Payment.objects.create(
            utilisateur=user,
            **validated_data
        )
        
        # Associer les objets liés
        if ticket:
            ticket.reference_paiement = payment.uuid
            ticket.save()
        
        if subscription:
            subscription.reference_paiement = payment.uuid
            subscription.save()
        
        return payment


class MomoTransactionSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour les transactions Mobile Money.
    """
    
    payment = PaymentSerializer(read_only=True)
    
    class Meta:
        model = MomoTransaction
        fields = [
            'id', 'payment', 'provider', 'transaction_id', 'status',
            'amount', 'currency', 'phone_number', 'external_reference',
            'callback_data', 'date_creation', 'date_completion',
            'error_code', 'error_message'
        ]
        read_only_fields = [
            'id', 'payment', 'transaction_id', 'status', 'external_reference',
            'callback_data', 'date_creation', 'date_completion',
            'error_code', 'error_message'
        ]


class CommissionSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour les commissions.
    """
    
    payment = PaymentSerializer(read_only=True)
    
    class Meta:
        model = Commission
        fields = [
            'id', 'payment', 'type_commission', 'montant_base',
            'pourcentage', 'montant_commission', 'statut',
            'date_creation', 'date_versement', 'reference_versement'
        ]
        read_only_fields = [
            'id', 'payment', 'montant_commission', 'date_creation',
            'date_versement', 'reference_versement'
        ]


class RefundSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour les remboursements.
    """
    
    payment = PaymentSerializer(read_only=True)
    demandeur = UserPublicSerializer(read_only=True)
    
    class Meta:
        model = Refund
        fields = [
            'id', 'payment', 'demandeur', 'montant', 'raison',
            'description', 'statut', 'date_demande', 'date_traitement',
            'reference_remboursement', 'commentaire_admin'
        ]
        read_only_fields = [
            'id', 'payment', 'demandeur', 'date_demande', 'date_traitement',
            'reference_remboursement'
        ]


class RefundCreateSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour créer une demande de remboursement.
    """
    
    payment_id = serializers.IntegerField()
    
    class Meta:
        model = Refund
        fields = ['payment_id', 'montant', 'raison', 'description']
    
    def validate_payment_id(self, value):
        """Valide le paiement."""
        try:
            payment = Payment.objects.get(
                id=value,
                utilisateur=self.context['request'].user,
                statut='REUSSI'
            )
        except Payment.DoesNotExist:
            raise serializers.ValidationError(
                "Paiement introuvable ou non éligible au remboursement"
            )
        
        # Vérifier qu'il n'y a pas déjà une demande en cours
        if Refund.objects.filter(
            payment=payment,
            statut__in=['EN_ATTENTE', 'APPROUVE']
        ).exists():
            raise serializers.ValidationError(
                "Une demande de remboursement est déjà en cours pour ce paiement"
            )
        
        return value
    
    def validate_montant(self, value):
        """Valide le montant du remboursement."""
        if value <= 0:
            raise serializers.ValidationError(
                "Le montant doit être supérieur à 0"
            )
        return value
    
    def validate(self, attrs):
        """Validation globale."""
        payment = Payment.objects.get(id=attrs['payment_id'])
        
        # Vérifier que le montant ne dépasse pas le paiement
        if attrs['montant'] > payment.montant:
            raise serializers.ValidationError(
                f"Le montant ne peut pas dépasser {payment.montant}"
            )
        
        attrs['payment'] = payment
        return attrs
    
    def create(self, validated_data):
        """Crée une demande de remboursement."""
        payment = validated_data.pop('payment')
        validated_data.pop('payment_id')
        
        return Refund.objects.create(
            payment=payment,
            demandeur=self.context['request'].user,
            **validated_data
        )


class PaymentStatsSerializer(serializers.Serializer):
    """
    Sérialiseur pour les statistiques de paiements.
    """
    
    total_payments = serializers.IntegerField()
    successful_payments = serializers.IntegerField()
    total_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_commissions = serializers.DecimalField(max_digits=15, decimal_places=2)
    payments_by_method = serializers.DictField()
    payments_by_status = serializers.DictField()
    recent_payments = PaymentSerializer(many=True)


class PaymentMethodStatsSerializer(serializers.Serializer):
    """
    Sérialiseur pour les statistiques par méthode de paiement.
    """
    
    method = serializers.CharField()
    count = serializers.IntegerField()
    total_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    success_rate = serializers.FloatField()


class WebhookDataSerializer(serializers.Serializer):
    """
    Sérialiseur pour les données de webhook.
    """
    
    transaction_id = serializers.CharField()
    status = serializers.CharField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    currency = serializers.CharField(required=False)
    reference = serializers.CharField(required=False)
    error_code = serializers.CharField(required=False)
    error_message = serializers.CharField(required=False)
    
    def validate_status(self, value):
        """Valide le statut."""
        valid_statuses = ['SUCCESS', 'FAILED', 'PENDING', 'CANCELLED']
        if value.upper() not in valid_statuses:
            raise serializers.ValidationError(f"Statut invalide: {value}")
        return value.upper()


class PaymentVerificationSerializer(serializers.Serializer):
    """
    Sérialiseur pour la vérification de paiement.
    """
    
    payment_uuid = serializers.UUIDField()
    verification_code = serializers.CharField(max_length=10, required=False)
    
    def validate_payment_uuid(self, value):
        """Valide l'UUID du paiement."""
        try:
            payment = Payment.objects.get(uuid=value)
        except Payment.DoesNotExist:
            raise serializers.ValidationError("Paiement introuvable")
        
        return value


class PaymentCancelSerializer(serializers.Serializer):
    """
    Sérialiseur pour annuler un paiement.
    """
    
    payment_uuid = serializers.UUIDField()
    reason = serializers.CharField(max_length=500, required=False)
    
    def validate_payment_uuid(self, value):
        """Valide que le paiement peut être annulé."""
        try:
            payment = Payment.objects.get(
                uuid=value,
                utilisateur=self.context['request'].user,
                statut='EN_ATTENTE'
            )
        except Payment.DoesNotExist:
            raise serializers.ValidationError(
                "Paiement introuvable ou ne peut pas être annulé"
            )
        
        return value


class PaymentRetrySerializer(serializers.Serializer):
    """
    Sérialiseur pour relancer un paiement échoué.
    """
    
    payment_uuid = serializers.UUIDField()
    new_phone_number = serializers.CharField(max_length=20, required=False)
    
    def validate_payment_uuid(self, value):
        """Valide que le paiement peut être relancé."""
        try:
            payment = Payment.objects.get(
                uuid=value,
                utilisateur=self.context['request'].user,
                statut='ECHEC'
            )
        except Payment.DoesNotExist:
            raise serializers.ValidationError(
                "Paiement introuvable ou ne peut pas être relancé"
            )
        
        return value
    
    def validate_new_phone_number(self, value):
        """Valide le nouveau numéro de téléphone."""
        if value and not value.startswith('+229'):
            raise serializers.ValidationError(
                "Le numéro doit commencer par +229"
            )
        return value

