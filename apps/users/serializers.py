"""
Sérialiseurs pour l'application users.

Ce module définit les sérialiseurs Django REST Framework pour
la sérialisation/désérialisation des modèles liés aux utilisateurs.
"""

from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import User, UserVerification, Follow


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour l'inscription d'un nouvel utilisateur.
    
    Gère la création d'un compte utilisateur avec validation
    des mots de passe et des données personnelles.
    """
    
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={'input_type': 'password'},
        help_text="Mot de passe (minimum 8 caractères)"
    )
    
    password_confirm = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        help_text="Confirmation du mot de passe"
    )
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'telephone', 'date_naissance'
        ]
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
            'telephone': {'required': True},
        }
    
    def validate_email(self, value):
        """Valide l'unicité de l'email."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "Un compte avec cet email existe déjà."
            )
        return value
    
    def validate_username(self, value):
        """Valide l'unicité du nom d'utilisateur."""
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError(
                "Ce nom d'utilisateur est déjà pris."
            )
        return value
    
    def validate_telephone(self, value):
        """Valide l'unicité du téléphone."""
        if User.objects.filter(telephone=value).exists():
            raise serializers.ValidationError(
                "Un compte avec ce numéro de téléphone existe déjà."
            )
        return value
    
    def validate(self, attrs):
        """Validation globale des données."""
        # Vérifier la correspondance des mots de passe
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': "Les mots de passe ne correspondent pas."
            })
        
        # Valider la force du mot de passe
        try:
            validate_password(attrs['password'])
        except ValidationError as e:
            raise serializers.ValidationError({
                'password': list(e.messages)
            })
        
        return attrs
    
    def create(self, validated_data):
        """Crée un nouvel utilisateur."""
        # Supprimer password_confirm des données
        validated_data.pop('password_confirm')
        
        # Créer l'utilisateur
        user = User.objects.create_user(**validated_data)
        return user


class UserLoginSerializer(serializers.Serializer):
    """
    Sérialiseur pour la connexion d'un utilisateur.
    
    Permet la connexion avec email/username et mot de passe.
    """
    
    login = serializers.CharField(
        help_text="Email ou nom d'utilisateur"
    )
    
    password = serializers.CharField(
        style={'input_type': 'password'},
        help_text="Mot de passe"
    )
    
    def validate(self, attrs):
        """Valide les identifiants de connexion."""
        login = attrs.get('login')
        password = attrs.get('password')
        
        if login and password:
            # Essayer de trouver l'utilisateur par email ou username
            user = None
            if '@' in login:
                try:
                    user = User.objects.get(email=login)
                except User.DoesNotExist:
                    pass
            else:
                try:
                    user = User.objects.get(username=login)
                except User.DoesNotExist:
                    pass
            
            if user:
                # Vérifier le mot de passe
                user = authenticate(username=user.username, password=password)
                if user:
                    if not user.is_active:
                        raise serializers.ValidationError(
                            "Ce compte a été désactivé."
                        )
                    attrs['user'] = user
                    return attrs
            
            raise serializers.ValidationError(
                "Identifiants incorrects."
            )
        else:
            raise serializers.ValidationError(
                "L'email/nom d'utilisateur et le mot de passe sont requis."
            )


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour le profil utilisateur.
    
    Permet la lecture et la modification des informations
    du profil utilisateur.
    """
    
    followers_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()
    events_count = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'telephone', 'date_naissance', 'photo_profil', 'bio',
            'est_verifie', 'date_verification', 'notifications_email',
            'notifications_push', 'date_creation', 'followers_count',
            'following_count', 'events_count'
        ]
        read_only_fields = [
            'id', 'username', 'email', 'est_verifie', 'date_verification',
            'date_creation', 'followers_count', 'following_count', 'events_count'
        ]
    
    def get_followers_count(self, obj):
        """Retourne le nombre de followers."""
        return obj.get_followers_count()
    
    def get_following_count(self, obj):
        """Retourne le nombre de personnes suivies."""
        return obj.get_following_count()
    
    def get_events_count(self, obj):
        """Retourne le nombre d'événements créés."""
        return obj.get_events_count()


class UserPublicSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour l'affichage public des utilisateurs.
    
    Contient uniquement les informations publiques
    d'un utilisateur.
    """
    
    followers_count = serializers.SerializerMethodField()
    events_count = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'first_name', 'last_name',
            'photo_profil', 'bio', 'est_verifie',
            'followers_count', 'events_count'
        ]
    
    def get_followers_count(self, obj):
        """Retourne le nombre de followers."""
        return obj.get_followers_count()
    
    def get_events_count(self, obj):
        """Retourne le nombre d'événements créés."""
        return obj.get_events_count()


class UserVerificationSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour les demandes de vérification d'utilisateur.
    
    Permet de soumettre une demande de vérification d'identité.
    """
    
    class Meta:
        model = UserVerification
        fields = [
            'id', 'statut', 'document_identite', 'document_selfie',
            'date_soumission', 'date_validation', 'commentaire_admin'
        ]
        read_only_fields = [
            'id', 'statut', 'date_soumission', 'date_validation',
            'commentaire_admin'
        ]
    
    def create(self, validated_data):
        """Crée une nouvelle demande de vérification."""
        validated_data['utilisateur'] = self.context['request'].user
        return super().create(validated_data)


class FollowSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour les relations de suivi.
    
    Gère les actions de follow/unfollow entre utilisateurs.
    """
    
    follower = UserPublicSerializer(read_only=True)
    following = UserPublicSerializer(read_only=True)
    
    class Meta:
        model = Follow
        fields = [
            'id', 'follower', 'following', 'date_suivi',
            'notifications_activees'
        ]
        read_only_fields = ['id', 'follower', 'following', 'date_suivi']


class FollowCreateSerializer(serializers.Serializer):
    """
    Sérialiseur pour créer une relation de suivi.
    """
    
    user_id = serializers.IntegerField(
        help_text="ID de l'utilisateur à suivre"
    )
    
    def validate_user_id(self, value):
        """Valide l'existence de l'utilisateur à suivre."""
        try:
            user = User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("Utilisateur introuvable.")
        
        # Vérifier qu'on ne se suit pas soi-même
        if user == self.context['request'].user:
            raise serializers.ValidationError(
                "Vous ne pouvez pas vous suivre vous-même."
            )
        
        # Vérifier qu'on ne suit pas déjà cet utilisateur
        if Follow.objects.filter(
            follower=self.context['request'].user,
            following=user
        ).exists():
            raise serializers.ValidationError(
                "Vous suivez déjà cet utilisateur."
            )
        
        return value
    
    def create(self, validated_data):
        """Crée une nouvelle relation de suivi."""
        following_user = User.objects.get(id=validated_data['user_id'])
        follow = Follow.objects.create(
            follower=self.context['request'].user,
            following=following_user
        )
        return follow


class PasswordChangeSerializer(serializers.Serializer):
    """
    Sérialiseur pour le changement de mot de passe.
    """
    
    old_password = serializers.CharField(
        style={'input_type': 'password'},
        help_text="Mot de passe actuel"
    )
    
    new_password = serializers.CharField(
        min_length=8,
        style={'input_type': 'password'},
        help_text="Nouveau mot de passe"
    )
    
    new_password_confirm = serializers.CharField(
        style={'input_type': 'password'},
        help_text="Confirmation du nouveau mot de passe"
    )
    
    def validate_old_password(self, value):
        """Valide l'ancien mot de passe."""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Mot de passe actuel incorrect.")
        return value
    
    def validate(self, attrs):
        """Validation globale."""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                'new_password_confirm': "Les nouveaux mots de passe ne correspondent pas."
            })
        
        # Valider la force du nouveau mot de passe
        try:
            validate_password(attrs['new_password'])
        except ValidationError as e:
            raise serializers.ValidationError({
                'new_password': list(e.messages)
            })
        
        return attrs
    
    def save(self):
        """Change le mot de passe de l'utilisateur."""
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user

