"""
Sérialiseurs pour l'application subscriptions.

Ce module définit les sérialiseurs Django REST Framework pour
le système d'abonnements.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from .models import SubscriptionPlan, Subscription, SubscriptionHistory
from apps.users.serializers import UserPublicSerializer

User = get_user_model()


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour les plans d'abonnement.
    """
    
    features_list = serializers.SerializerMethodField()
    is_popular = serializers.SerializerMethodField()
    
    class Meta:
        model = SubscriptionPlan
        fields = [
            'id', 'nom', 'description', 'prix', 'duree_jours',
            'limite_evenements', 'limite_participants', 'limite_photos',
            'support_prioritaire', 'analytics_avances', 'promotion_premium',
            'badge_verifie', 'features', 'features_list', 'actif',
            'date_creation', 'is_popular'
        ]
        read_only_fields = ['id', 'date_creation']
    
    def get_features_list(self, obj):
        """Retourne les fonctionnalités sous forme de liste."""
        if obj.features:
            return obj.features.get('features', [])
        return []
    
    def get_is_popular(self, obj):
        """Détermine si le plan est populaire (exemple: plan Premium)."""
        return obj.nom.lower() == 'premium'


class SubscriptionSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour les abonnements.
    """
    
    utilisateur = UserPublicSerializer(read_only=True)
    plan = SubscriptionPlanSerializer(read_only=True)
    days_remaining = serializers.SerializerMethodField()
    is_expired = serializers.SerializerMethodField()
    can_renew = serializers.SerializerMethodField()
    
    class Meta:
        model = Subscription
        fields = [
            'id', 'utilisateur', 'plan', 'date_debut', 'date_fin',
            'statut', 'renouvellement_auto', 'reference_paiement',
            'date_creation', 'date_modification', 'days_remaining',
            'is_expired', 'can_renew'
        ]
        read_only_fields = [
            'id', 'utilisateur', 'date_creation', 'date_modification'
        ]
    
    def get_days_remaining(self, obj):
        """Retourne le nombre de jours restants."""
        if obj.statut == 'ACTIF' and obj.date_fin:
            remaining = (obj.date_fin - timezone.now().date()).days
            return max(0, remaining)
        return 0
    
    def get_is_expired(self, obj):
        """Vérifie si l'abonnement a expiré."""
        if obj.date_fin:
            return timezone.now().date() > obj.date_fin
        return False
    
    def get_can_renew(self, obj):
        """Vérifie si l'abonnement peut être renouvelé."""
        return obj.statut in ['ACTIF', 'EXPIRE'] and obj.plan.actif


class SubscriptionCreateSerializer(serializers.Serializer):
    """
    Sérialiseur pour créer un abonnement.
    """
    
    plan_id = serializers.IntegerField()
    renouvellement_auto = serializers.BooleanField(default=False)
    
    def validate_plan_id(self, value):
        """Valide le plan d'abonnement."""
        try:
            plan = SubscriptionPlan.objects.get(id=value, actif=True)
        except SubscriptionPlan.DoesNotExist:
            raise serializers.ValidationError(
                "Plan d'abonnement introuvable ou inactif"
            )
        return value
    
    def validate(self, attrs):
        """Validation globale."""
        user = self.context['request'].user
        plan_id = attrs['plan_id']
        
        # Vérifier qu'il n'y a pas déjà un abonnement actif
        active_subscription = Subscription.objects.filter(
            utilisateur=user,
            statut='ACTIF'
        ).first()
        
        if active_subscription:
            raise serializers.ValidationError(
                "Vous avez déjà un abonnement actif. "
                "Annulez-le d'abord ou attendez son expiration."
            )
        
        # Vérifier qu'il n'y a pas d'abonnement en attente de paiement
        pending_subscription = Subscription.objects.filter(
            utilisateur=user,
            statut='EN_ATTENTE'
        ).first()
        
        if pending_subscription:
            raise serializers.ValidationError(
                "Vous avez déjà un abonnement en attente de paiement."
            )
        
        attrs['plan'] = SubscriptionPlan.objects.get(id=plan_id)
        return attrs
    
    def create(self, validated_data):
        """Crée un nouvel abonnement."""
        user = self.context['request'].user
        plan = validated_data['plan']
        renouvellement_auto = validated_data['renouvellement_auto']
        
        # Calculer les dates
        date_debut = timezone.now().date()
        date_fin = date_debut + timedelta(days=plan.duree_jours)
        
        # Créer l'abonnement
        subscription = Subscription.objects.create(
            utilisateur=user,
            plan=plan,
            date_debut=date_debut,
            date_fin=date_fin,
            statut='EN_ATTENTE',  # En attente de paiement
            renouvellement_auto=renouvellement_auto
        )
        
        return subscription


class SubscriptionUpdateSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour mettre à jour un abonnement.
    """
    
    class Meta:
        model = Subscription
        fields = ['renouvellement_auto']


class SubscriptionHistorySerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour l'historique des abonnements.
    """
    
    utilisateur = UserPublicSerializer(read_only=True)
    plan = SubscriptionPlanSerializer(read_only=True)
    
    class Meta:
        model = SubscriptionHistory
        fields = [
            'id', 'utilisateur', 'plan', 'action', 'date_debut',
            'date_fin', 'montant_paye', 'reference_paiement',
            'date_action', 'details'
        ]
        read_only_fields = [
            'id', 'utilisateur', 'plan', 'date_action'
        ]


class SubscriptionStatsSerializer(serializers.Serializer):
    """
    Sérialiseur pour les statistiques d'abonnements.
    """
    
    total_subscriptions = serializers.IntegerField()
    active_subscriptions = serializers.IntegerField()
    expired_subscriptions = serializers.IntegerField()
    revenue_this_month = serializers.DecimalField(max_digits=15, decimal_places=2)
    revenue_total = serializers.DecimalField(max_digits=15, decimal_places=2)
    subscriptions_by_plan = serializers.DictField()
    recent_subscriptions = SubscriptionSerializer(many=True)


class SubscriptionRenewalSerializer(serializers.Serializer):
    """
    Sérialiseur pour le renouvellement d'abonnement.
    """
    
    subscription_id = serializers.IntegerField()
    new_plan_id = serializers.IntegerField(required=False)
    
    def validate_subscription_id(self, value):
        """Valide l'abonnement."""
        try:
            subscription = Subscription.objects.get(
                id=value,
                utilisateur=self.context['request'].user
            )
        except Subscription.DoesNotExist:
            raise serializers.ValidationError(
                "Abonnement introuvable"
            )
        
        if subscription.statut not in ['ACTIF', 'EXPIRE']:
            raise serializers.ValidationError(
                "Cet abonnement ne peut pas être renouvelé"
            )
        
        return value
    
    def validate_new_plan_id(self, value):
        """Valide le nouveau plan si fourni."""
        if value:
            try:
                plan = SubscriptionPlan.objects.get(id=value, actif=True)
            except SubscriptionPlan.DoesNotExist:
                raise serializers.ValidationError(
                    "Plan d'abonnement introuvable ou inactif"
                )
        return value
    
    def validate(self, attrs):
        """Validation globale."""
        subscription = Subscription.objects.get(id=attrs['subscription_id'])
        
        # Si pas de nouveau plan, utiliser le plan actuel
        if 'new_plan_id' not in attrs or not attrs['new_plan_id']:
            attrs['new_plan'] = subscription.plan
        else:
            attrs['new_plan'] = SubscriptionPlan.objects.get(
                id=attrs['new_plan_id']
            )
        
        attrs['subscription'] = subscription
        return attrs


class SubscriptionCancelSerializer(serializers.Serializer):
    """
    Sérialiseur pour l'annulation d'abonnement.
    """
    
    subscription_id = serializers.IntegerField()
    reason = serializers.CharField(max_length=500, required=False)
    cancel_immediately = serializers.BooleanField(default=False)
    
    def validate_subscription_id(self, value):
        """Valide l'abonnement."""
        try:
            subscription = Subscription.objects.get(
                id=value,
                utilisateur=self.context['request'].user,
                statut='ACTIF'
            )
        except Subscription.DoesNotExist:
            raise serializers.ValidationError(
                "Abonnement actif introuvable"
            )
        
        return value


class SubscriptionUpgradeSerializer(serializers.Serializer):
    """
    Sérialiseur pour la mise à niveau d'abonnement.
    """
    
    subscription_id = serializers.IntegerField()
    new_plan_id = serializers.IntegerField()
    
    def validate_subscription_id(self, value):
        """Valide l'abonnement."""
        try:
            subscription = Subscription.objects.get(
                id=value,
                utilisateur=self.context['request'].user,
                statut='ACTIF'
            )
        except Subscription.DoesNotExist:
            raise serializers.ValidationError(
                "Abonnement actif introuvable"
            )
        
        return value
    
    def validate_new_plan_id(self, value):
        """Valide le nouveau plan."""
        try:
            plan = SubscriptionPlan.objects.get(id=value, actif=True)
        except SubscriptionPlan.DoesNotExist:
            raise serializers.ValidationError(
                "Plan d'abonnement introuvable ou inactif"
            )
        return value
    
    def validate(self, attrs):
        """Validation globale."""
        subscription = Subscription.objects.get(id=attrs['subscription_id'])
        new_plan = SubscriptionPlan.objects.get(id=attrs['new_plan_id'])
        
        # Vérifier que c'est bien une mise à niveau
        if new_plan.prix <= subscription.plan.prix:
            raise serializers.ValidationError(
                "Le nouveau plan doit être plus cher que le plan actuel"
            )
        
        attrs['subscription'] = subscription
        attrs['new_plan'] = new_plan
        return attrs


class SubscriptionUsageSerializer(serializers.Serializer):
    """
    Sérialiseur pour l'utilisation de l'abonnement.
    """
    
    events_created = serializers.IntegerField()
    events_limit = serializers.IntegerField()
    participants_total = serializers.IntegerField()
    participants_limit = serializers.IntegerField()
    photos_uploaded = serializers.IntegerField()
    photos_limit = serializers.IntegerField()
    usage_percentage = serializers.FloatField()
    warnings = serializers.ListField(child=serializers.CharField())


class SubscriptionBenefitsSerializer(serializers.Serializer):
    """
    Sérialiseur pour les avantages de l'abonnement.
    """
    
    plan_name = serializers.CharField()
    features = serializers.ListField(child=serializers.CharField())
    limits = serializers.DictField()
    premium_features = serializers.ListField(child=serializers.CharField())
    support_level = serializers.CharField()


class SubscriptionComparisonSerializer(serializers.Serializer):
    """
    Sérialiseur pour comparer les plans d'abonnement.
    """
    
    plans = SubscriptionPlanSerializer(many=True)
    current_plan = SubscriptionPlanSerializer(required=False, allow_null=True)
    recommendations = serializers.ListField(child=serializers.CharField())


class SubscriptionPaymentSerializer(serializers.Serializer):
    """
    Sérialiseur pour le paiement d'abonnement.
    """
    
    subscription_id = serializers.IntegerField()
    payment_method = serializers.ChoiceField(
        choices=['ORANGE_MONEY', 'MTN_MONEY', 'MOOV_MONEY']
    )
    phone_number = serializers.CharField(max_length=20)
    
    def validate_subscription_id(self, value):
        """Valide l'abonnement."""
        try:
            subscription = Subscription.objects.get(
                id=value,
                utilisateur=self.context['request'].user,
                statut='EN_ATTENTE'
            )
        except Subscription.DoesNotExist:
            raise serializers.ValidationError(
                "Abonnement en attente de paiement introuvable"
            )
        
        return value
    
    def validate_phone_number(self, value):
        """Valide le numéro de téléphone."""
        if not value.startswith('+225'):
            raise serializers.ValidationError(
                "Le numéro doit commencer par +225"
            )
        if len(value) != 13:
            raise serializers.ValidationError(
                "Format invalide. Utilisez +225XXXXXXXX"
            )
        return value

