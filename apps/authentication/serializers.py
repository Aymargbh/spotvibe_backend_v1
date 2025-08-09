"""
Sérialiseurs pour l'application authentication.

Ce module définit les sérialiseurs Django REST Framework pour
l'authentification avancée et les connexions sociales.
"""

from rest_framework import serializers
from django.contrib.auth import authenticate, get_user_model
from django.core.exceptions import ValidationError
from .models import SocialAccount, LoginAttempt
from apps.users.serializers import UserPublicSerializer
import facebook
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from django.conf import settings

User = get_user_model()


class SocialAccountSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour les comptes sociaux.
    """
    
    utilisateur = UserPublicSerializer(read_only=True)
    
    class Meta:
        model = SocialAccount
        fields = [
            'id', 'utilisateur', 'provider', 'social_id', 'email',
            'nom_complet', 'photo_url', 'date_creation', 'actif'
        ]
        read_only_fields = [
            'id', 'utilisateur', 'social_id', 'date_creation'
        ]


class GoogleAuthSerializer(serializers.Serializer):
    """Sérialiseur pour l'authentification Google."""
    
    access_token = serializers.CharField()
    
    def validate_access_token(self, value):
        """Valide le token d'accès Google."""
        try:
            idinfo = id_token.verify_oauth2_token(
                value,
                google_requests.Request(),
                settings.SPOTVIBE_SETTINGS['GOOGLE_OAUTH2_CLIENT_ID']
            )

            if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                raise serializers.ValidationError("Token émis par un fournisseur non autorisé")

            return value
        except Exception as e:
            raise serializers.ValidationError(f"Token Google invalide: {str(e)}")
    
    def create(self, validated_data):
        """Crée ou récupère un utilisateur via Google."""
        token = validated_data['access_token']
        
        # Récupérer les infos utilisateur depuis Google
        idinfo = id_token.verify_oauth2_token(
            token,
            google_requests.Request(),
            settings.SPOTVIBE_SETTINGS['GOOGLE_OAUTH2_CLIENT_ID']
        )
        
        google_user_data = {
            'id': idinfo['sub'],
            'email': idinfo['email'],
            'name': idinfo.get('name', ''),
            'picture': idinfo.get('picture', '')
        }
        
        # Chercher ou créer le compte social
        social_account, created = SocialAccount.objects.get_or_create(
            provider='GOOGLE',
            social_id=google_user_data['id'],
            defaults={
                'email': google_user_data['email'],
                'nom_complet': google_user_data['name'],
                'photo_url': google_user_data['picture']
            }
        )

        # Chercher ou créer l'utilisateur
        if social_account.utilisateur:
            user = social_account.utilisateur
        else:
            # Créer un nouvel utilisateur
            username = google_user_data['email'].split('@')[0]
            # S'assurer que le username est unique
            counter = 1
            original_username = username
            while User.objects.filter(username=username).exists():
                username = f"{original_username}{counter}"
                counter += 1
            
            user = User.objects.create_user(
                username=username,
                email=google_user_data['email'],
                first_name=google_user_data['name'].split()[0],
                last_name=' '.join(google_user_data['name'].split()[1:]),
                telephone=f"+229{counter:10d}"  # Téléphone temporaire
            )
            
            social_account.utilisateur = user
            social_account.save()
        
        return user


class FacebookAuthSerializer(serializers.Serializer):
    """Sérialiseur pour l'authentification Facebook."""
    
    access_token = serializers.CharField()
    
    def validate_access_token(self, value):
        """Valide le token d'accès Facebook."""
        try:
            graph = facebook.GraphAPI(access_token=value, version='3.1')
            # Vérifie si le token est valide en récupérant les infos utilisateur
            user_info = graph.get_object('me', fields='id,email,name,picture')
            return value
        except Exception as e:
            raise serializers.ValidationError(f"Token Facebook invalide: {str(e)}")
    
    def create(self, validated_data):
        """Crée ou récupère un utilisateur via Facebook."""
        token = validated_data['access_token']
        
        # Récupérer les infos utilisateur depuis Facebook
        graph = facebook.GraphAPI(access_token=token, version='3.1')
        facebook_user_data = graph.get_object(
            'me',
            fields='id,email,name,picture.type(large)'
        )
        
        # Chercher ou créer le compte social
        social_account, created = SocialAccount.objects.get_or_create(
            provider='FACEBOOK',
            social_id=facebook_user_data['id'],
            defaults={
                'email': facebook_user_data.get('email', ''),
                'nom_complet': facebook_user_data.get('name', ''),
                'photo_url': facebook_user_data.get('picture', {}).get('data', {}).get('url', '')
            }
        )
        
        # Chercher ou créer l'utilisateur
        if social_account.utilisateur:
            user = social_account.utilisateur
        else:
            # Créer un nouvel utilisateur
            username = facebook_user_data['email'].split('@')[0]
            counter = 1
            original_username = username
            while User.objects.filter(username=username).exists():
                username = f"{original_username}{counter}"
                counter += 1
            
            user = User.objects.create_user(
                username=username,
                email=facebook_user_data['email'],
                first_name=facebook_user_data['name'].split()[0],
                last_name=' '.join(facebook_user_data['name'].split()[1:]),
                telephone=f"+229{counter:10d}"
            )
            
            social_account.utilisateur = user
            social_account.save()
        
        return user


class LoginAttemptSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour les tentatives de connexion.
    """
    
    utilisateur = UserPublicSerializer(read_only=True)
    
    class Meta:
        model = LoginAttempt
        fields = [
            'id', 'utilisateur', 'adresse_ip', 'user_agent',
            'reussi', 'date_tentative', 'raison_echec'
        ]
        read_only_fields = ['id', 'date_tentative']


class TwoFactorSetupSerializer(serializers.Serializer):
    """
    Sérialiseur pour la configuration de l'authentification à deux facteurs.
    """
    
    phone_number = serializers.CharField(max_length=20)
    
    def validate_phone_number(self, value):
        """Valide le numéro de téléphone."""
        if not value.startswith('+229'):
            raise serializers.ValidationError(
                "Le numéro doit commencer par +229"
            )
        if len(value) != 15:
            raise serializers.ValidationError(
                "Le numéro doit contenir 15 caractères (+229XXXXXXXX)"
            )
        return value


class TwoFactorVerifySerializer(serializers.Serializer):
    """
    Sérialiseur pour la vérification du code 2FA.
    """
    
    code = serializers.CharField(max_length=6, min_length=6)
    
    def validate_code(self, value):
        """Valide le code 2FA."""
        if not value.isdigit():
            raise serializers.ValidationError(
                "Le code doit contenir uniquement des chiffres"
            )
        return value


class PasswordResetRequestSerializer(serializers.Serializer):
    """
    Sérialiseur pour la demande de réinitialisation de mot de passe.
    """
    
    email = serializers.EmailField()
    
    def validate_email(self, value):
        """Valide que l'email existe."""
        try:
            User.objects.get(email=value, is_active=True)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                "Aucun compte actif trouvé avec cette adresse email"
            )
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Sérialiseur pour la confirmation de réinitialisation de mot de passe.
    """
    
    token = serializers.CharField()
    new_password = serializers.CharField(min_length=8)
    new_password_confirm = serializers.CharField(min_length=8)
    
    def validate(self, attrs):
        """Validation globale."""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError(
                "Les mots de passe ne correspondent pas"
            )
        return attrs
    
    def validate_new_password(self, value):
        """Valide la force du mot de passe."""
        if len(value) < 8:
            raise serializers.ValidationError(
                "Le mot de passe doit contenir au moins 8 caractères"
            )
        
        if not any(c.isdigit() for c in value):
            raise serializers.ValidationError(
                "Le mot de passe doit contenir au moins un chiffre"
            )
        
        if not any(c.isupper() for c in value):
            raise serializers.ValidationError(
                "Le mot de passe doit contenir au moins une majuscule"
            )
        
        return value


class AccountActivationSerializer(serializers.Serializer):
    """
    Sérialiseur pour l'activation de compte.
    """
    
    token = serializers.CharField()
    
    def validate_token(self, value):
        """Valide le token d'activation."""
        if not value or len(value) < 20:
            raise serializers.ValidationError("Token d'activation invalide")
        return value

