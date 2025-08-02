"""
Sérialiseurs pour l'application events.

Ce module définit les sérialiseurs Django REST Framework pour
la sérialisation/désérialisation des modèles liés aux événements.
"""

from rest_framework import serializers
from django.utils import timezone
from django.core.exceptions import ValidationError
from .models import Event, EventCategory, EventParticipation, EventShare, EventTicket
from apps.users.serializers import UserPublicSerializer


class EventCategorySerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour les catégories d'événements.
    """
    
    events_count = serializers.SerializerMethodField()
    
    class Meta:
        model = EventCategory
        fields = [
            'id', 'nom', 'description', 'couleur', 'icone',
            'ordre', 'actif', 'events_count'
        ]
    
    def get_events_count(self, obj):
        """Retourne le nombre d'événements dans cette catégorie."""
        return obj.get_events_count()


class EventCreateSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour la création d'événements.
    """
    
    class Meta:
        model = Event
        fields = [
            'titre', 'description', 'description_courte', 'categorie',
            'date_debut', 'date_fin', 'lieu', 'adresse', 'latitude',
            'longitude', 'type_acces', 'prix', 'capacite_max',
            'image_couverture', 'billetterie_activee', 'commission_billetterie'
        ]
    
    def validate_date_debut(self, value):
        """Valide que la date de début est dans le futur."""
        if value <= timezone.now():
            raise serializers.ValidationError(
                "La date de début doit être dans le futur."
            )
        return value
    
    def validate_date_fin(self, value):
        """Valide que la date de fin est cohérente."""
        date_debut = self.initial_data.get('date_debut')
        if date_debut and value <= timezone.datetime.fromisoformat(date_debut.replace('Z', '+00:00')):
            raise serializers.ValidationError(
                "La date de fin doit être après la date de début."
            )
        return value
    
    def validate_prix(self, value):
        """Valide le prix selon le type d'accès."""
        type_acces = self.initial_data.get('type_acces')
        if type_acces == 'GRATUIT' and value > 0:
            raise serializers.ValidationError(
                "Le prix doit être 0 pour un événement gratuit."
            )
        elif type_acces == 'PAYANT' and value <= 0:
            raise serializers.ValidationError(
                "Le prix doit être supérieur à 0 pour un événement payant."
            )
        return value
    
    def validate_capacite_max(self, value):
        """Valide la capacité maximale."""
        if value <= 0:
            raise serializers.ValidationError(
                "La capacité maximale doit être supérieure à 0."
            )
        return value
    
    def create(self, validated_data):
        """Crée un nouvel événement."""
        validated_data['createur'] = self.context['request'].user
        return super().create(validated_data)


class EventSerializer(serializers.ModelSerializer):
    """
    Sérialiseur complet pour les événements.
    """
    
    createur = UserPublicSerializer(read_only=True)
    categorie = EventCategorySerializer(read_only=True)
    participants_count = serializers.SerializerMethodField()
    is_participating = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()
    revenue = serializers.SerializerMethodField()
    commission_amount = serializers.SerializerMethodField()
    
    class Meta:
        model = Event
        fields = [
            'id', 'titre', 'description', 'description_courte', 'createur',
            'categorie', 'date_debut', 'date_fin', 'lieu', 'adresse',
            'latitude', 'longitude', 'lien_google_maps', 'type_acces',
            'prix', 'capacite_max', 'image_couverture', 'billetterie_activee',
            'commission_billetterie', 'statut', 'date_creation',
            'date_modification', 'nombre_vues', 'nombre_partages',
            'participants_count', 'is_participating', 'is_liked',
            'can_edit', 'revenue', 'commission_amount'
        ]
        read_only_fields = [
            'id', 'createur', 'statut', 'date_creation', 'date_modification',
            'nombre_vues', 'nombre_partages', 'lien_google_maps'
        ]
    
    def get_participants_count(self, obj):
        """Retourne le nombre de participants."""
        return obj.get_participants_count()
    
    def get_is_participating(self, obj):
        """Vérifie si l'utilisateur participe à l'événement."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.participations.filter(
                utilisateur=request.user,
                statut='CONFIRME'
            ).exists()
        return False
    
    def get_is_liked(self, obj):
        """Vérifie si l'utilisateur a liké l'événement."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.participations.filter(
                utilisateur=request.user,
                statut='INTERESSE'
            ).exists()
        return False
    
    def get_can_edit(self, obj):
        """Vérifie si l'utilisateur peut modifier l'événement."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return (
                obj.createur == request.user or
                request.user.is_staff
            )
        return False
    
    def get_revenue(self, obj):
        """Retourne le revenu de l'événement."""
        return obj.get_revenue()
    
    def get_commission_amount(self, obj):
        """Retourne le montant de commission."""
        return obj.get_commission_amount()


class EventListSerializer(serializers.ModelSerializer):
    """
    Sérialiseur simplifié pour la liste des événements.
    """
    
    createur = UserPublicSerializer(read_only=True)
    categorie = EventCategorySerializer(read_only=True)
    participants_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Event
        fields = [
            'id', 'titre', 'description_courte', 'createur', 'categorie',
            'date_debut', 'date_fin', 'lieu', 'type_acces', 'prix',
            'image_couverture', 'statut', 'participants_count'
        ]
    
    def get_participants_count(self, obj):
        """Retourne le nombre de participants."""
        return obj.get_participants_count()


class EventParticipationSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour les participations aux événements.
    """
    
    utilisateur = UserPublicSerializer(read_only=True)
    evenement = EventListSerializer(read_only=True)
    
    class Meta:
        model = EventParticipation
        fields = [
            'id', 'utilisateur', 'evenement', 'statut',
            'date_participation', 'date_modification'
        ]
        read_only_fields = [
            'id', 'utilisateur', 'evenement', 'date_participation',
            'date_modification'
        ]


class EventParticipationCreateSerializer(serializers.Serializer):
    """
    Sérialiseur pour créer une participation à un événement.
    """
    
    event_id = serializers.IntegerField()
    statut = serializers.ChoiceField(
        choices=['INTERESSE', 'CONFIRME'],
        default='CONFIRME'
    )
    
    def validate_event_id(self, value):
        """Valide l'existence de l'événement."""
        try:
            event = Event.objects.get(id=value, statut='VALIDE')
        except Event.DoesNotExist:
            raise serializers.ValidationError("Événement introuvable ou non validé.")
        
        # Vérifier que l'événement n'est pas passé
        if event.date_debut <= timezone.now():
            raise serializers.ValidationError("Cet événement est déjà passé.")
        
        # Vérifier la capacité
        if event.capacite_max and event.get_participants_count() >= event.capacite_max:
            raise serializers.ValidationError("Cet événement est complet.")
        
        return value
    
    def create(self, validated_data):
        """Crée ou met à jour une participation."""
        event = Event.objects.get(id=validated_data['event_id'])
        user = self.context['request'].user
        
        participation, created = EventParticipation.objects.update_or_create(
            utilisateur=user,
            evenement=event,
            defaults={'statut': validated_data['statut']}
        )
        
        return participation


class EventShareSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour les partages d'événements.
    """
    
    utilisateur = UserPublicSerializer(read_only=True)
    evenement = EventListSerializer(read_only=True)
    
    class Meta:
        model = EventShare
        fields = [
            'id', 'utilisateur', 'evenement', 'plateforme',
            'lien_genere', 'nombre_clics', 'date_partage'
        ]
        read_only_fields = [
            'id', 'utilisateur', 'evenement', 'lien_genere',
            'nombre_clics', 'date_partage'
        ]


class EventShareCreateSerializer(serializers.Serializer):
    """
    Sérialiseur pour créer un partage d'événement.
    """
    
    event_id = serializers.IntegerField()
    plateforme = serializers.ChoiceField(
        choices=['FACEBOOK', 'TWITTER', 'WHATSAPP', 'TELEGRAM', 'EMAIL', 'LIEN']
    )
    
    def validate_event_id(self, value):
        """Valide l'existence de l'événement."""
        try:
            Event.objects.get(id=value, statut='VALIDE')
        except Event.DoesNotExist:
            raise serializers.ValidationError("Événement introuvable ou non validé.")
        return value
    
    def create(self, validated_data):
        """Crée un partage d'événement."""
        event = Event.objects.get(id=validated_data['event_id'])
        user = self.context['request'].user
        
        share = EventShare.objects.create(
            utilisateur=user,
            evenement=event,
            plateforme=validated_data['plateforme']
        )
        
        # Incrémenter le compteur de partages de l'événement
        event.nombre_partages += 1
        event.save(update_fields=['nombre_partages'])
        
        return share


class EventTicketSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour les billets d'événements.
    """
    
    utilisateur = UserPublicSerializer(read_only=True)
    evenement = EventListSerializer(read_only=True)
    total_price = serializers.SerializerMethodField()
    
    class Meta:
        model = EventTicket
        fields = [
            'id', 'uuid', 'utilisateur', 'evenement', 'prix',
            'quantite', 'total_price', 'statut', 'date_achat',
            'date_utilisation', 'code_qr', 'reference_paiement'
        ]
        read_only_fields = [
            'id', 'uuid', 'utilisateur', 'evenement', 'statut',
            'date_achat', 'date_utilisation', 'code_qr'
        ]
    
    def get_total_price(self, obj):
        """Retourne le prix total du billet."""
        return obj.get_total_price()


class EventTicketCreateSerializer(serializers.Serializer):
    """
    Sérialiseur pour acheter un billet d'événement.
    """
    
    event_id = serializers.IntegerField()
    quantite = serializers.IntegerField(min_value=1, max_value=10)
    
    def validate_event_id(self, value):
        """Valide l'événement pour l'achat de billets."""
        try:
            event = Event.objects.get(id=value, statut='VALIDE')
        except Event.DoesNotExist:
            raise serializers.ValidationError("Événement introuvable ou non validé.")
        
        # Vérifier que la billetterie est activée
        if not event.billetterie_activee:
            raise serializers.ValidationError("La billetterie n'est pas activée pour cet événement.")
        
        # Vérifier que l'événement est payant
        if event.type_acces != 'PAYANT':
            raise serializers.ValidationError("Cet événement ne nécessite pas de billet.")
        
        # Vérifier que l'événement n'est pas passé
        if event.date_debut <= timezone.now():
            raise serializers.ValidationError("Cet événement est déjà passé.")
        
        return value
    
    def validate(self, attrs):
        """Validation globale."""
        event = Event.objects.get(id=attrs['event_id'])
        quantite = attrs['quantite']
        
        # Vérifier la capacité disponible
        if event.capacite_max:
            billets_vendus = EventTicket.objects.filter(
                evenement=event,
                statut__in=['VALIDE', 'UTILISE']
            ).aggregate(
                total=models.Sum('quantite')
            )['total'] or 0
            
            if billets_vendus + quantite > event.capacite_max:
                places_restantes = event.capacite_max - billets_vendus
                raise serializers.ValidationError(
                    f"Seulement {places_restantes} place(s) disponible(s)."
                )
        
        return attrs
    
    def create(self, validated_data):
        """Crée un billet d'événement."""
        event = Event.objects.get(id=validated_data['event_id'])
        user = self.context['request'].user
        
        ticket = EventTicket.objects.create(
            utilisateur=user,
            evenement=event,
            prix=event.prix,
            quantite=validated_data['quantite']
        )
        
        return ticket

