"""
Vues pour l'application authentication.

Ce module définit les vues Django REST Framework pour
l'authentification avancée et les connexions sociales.
"""

from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import get_user_model, login
from django.core.mail import send_mail
from django.conf import settings
from django.utils.crypto import get_random_string
from django.utils import timezone
from datetime import timedelta
import secrets
import logging

from .models import SocialAccount, LoginAttempt
from .serializers import (
    SocialAccountSerializer, GoogleAuthSerializer, FacebookAuthSerializer,
    LoginAttemptSerializer, TwoFactorSetupSerializer, TwoFactorVerifySerializer,
    PasswordResetRequestSerializer, PasswordResetConfirmSerializer,
    AccountActivationSerializer
)
from apps.users.serializers import UserProfileSerializer

User = get_user_model()
logger = logging.getLogger(__name__)


class GoogleAuthView(generics.CreateAPIView):
    """
    Vue pour l'authentification Google OAuth.
    
    POST /api/auth/google/
    """
    
    serializer_class = GoogleAuthSerializer
    permission_classes = [permissions.AllowAny]
    
    def create(self, request, *args, **kwargs):
        """Authentifie un utilisateur via Google."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            user = serializer.save()
            
            # Créer ou récupérer le token
            token, created = Token.objects.get_or_create(user=user)
            
            # Connecter l'utilisateur
            login(request, user)
            
            # Enregistrer la tentative de connexion
            LoginAttempt.objects.create(
                utilisateur=user,
                adresse_ip=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                statut="REUSSI"
            )
            
            return Response({
                'message': 'Connexion Google réussie',
                'user': UserProfileSerializer(user).data,
                'token': token.key
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f'Google auth error: {e}')
            return Response({
                'error': 'Erreur lors de l\'authentification Google'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    def get_client_ip(self, request):
        """Récupère l'adresse IP du client."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class FacebookAuthView(generics.CreateAPIView):
    """
    Vue pour l'authentification Facebook OAuth.
    
    POST /api/auth/facebook/
    """
    
    serializer_class = FacebookAuthSerializer
    permission_classes = [permissions.AllowAny]
    
    def create(self, request, *args, **kwargs):
        """Authentifie un utilisateur via Facebook."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            user = serializer.save()
            
            # Créer ou récupérer le token
            token, created = Token.objects.get_or_create(user=user)
            
            # Connecter l'utilisateur
            login(request, user)
            
            # Enregistrer la tentative de connexion
            LoginAttempt.objects.create(
                utilisateur=user,
                adresse_ip=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                statut="REUSSI"
            )
            
            return Response({
                'message': 'Connexion Facebook réussie',
                'user': UserProfileSerializer(user).data,
                'token': token.key
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f'Facebook auth error: {e}')
            return Response({
                'error': 'Erreur lors de l\'authentification Facebook'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    def get_client_ip(self, request):
        """Récupère l'adresse IP du client."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class SocialAccountListView(generics.ListAPIView):
    """
    Vue pour lister les comptes sociaux de l'utilisateur.
    
    GET /api/auth/social-accounts/
    """
    
    serializer_class = SocialAccountSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Retourne les comptes sociaux de l'utilisateur."""
        return SocialAccount.objects.filter(
            utilisateur=self.request.user,
            actif=True
        )


@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def disconnect_social_account(request, provider):
    """
    Vue pour déconnecter un compte social.
    
    DELETE /api/auth/social-accounts/{provider}/disconnect/
    """
    
    try:
        social_account = SocialAccount.objects.get(
            utilisateur=request.user,
            provider=provider.upper(),
            actif=True
        )
        
        social_account.actif = False
        social_account.save()
        
        return Response({
            'message': f'Compte {provider} déconnecté avec succès'
        }, status=status.HTTP_200_OK)
        
    except SocialAccount.DoesNotExist:
        return Response({
            'error': f'Aucun compte {provider} connecté trouvé'
        }, status=status.HTTP_404_NOT_FOUND)


class LoginAttemptListView(generics.ListAPIView):
    """
    Vue pour lister les tentatives de connexion de l'utilisateur.
    
    GET /api/auth/login-attempts/
    """
    
    serializer_class = LoginAttemptSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Retourne les tentatives de connexion de l'utilisateur."""
        return LoginAttempt.objects.filter(
            utilisateur=self.request.user
        ).order_by('-date_tentative')[:20]


class TwoFactorSetupView(generics.CreateAPIView):
    """
    Vue pour configurer l'authentification à deux facteurs.
    
    POST /api/auth/2fa/setup/
    """
    
    serializer_class = TwoFactorSetupSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        """Configure l'authentification à deux facteurs."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        phone_number = serializer.validated_data['phone_number']
        
        # Générer un code de vérification
        verification_code = get_random_string(6, allowed_chars='0123456789')
        
        # Créer un objet TwoFactorAuth
        two_factor_auth = TwoFactorAuth.objects.create(
            utilisateur=request.user,
            phone_number=phone_number,
            verification_code=verification_code,
            date_expiration=timezone.now() + timedelta(minutes=5)
        )
        
        # Envoyer le code par SMS (simulation)
        # En production, intégrez un service SMS comme Twilio
        logger.info(f'Code 2FA pour {phone_number}: {verification_code}')
        
        return Response({
            'message': 'Code de vérification envoyé par SMS',
            'phone_number': phone_number
        }, status=status.HTTP_200_OK)


class TwoFactorVerifyView(generics.CreateAPIView):
    """
    Vue pour vérifier le code 2FA.
    
    POST /api/auth/2fa/verify/
    """
    
    serializer_class = TwoFactorVerifySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        """Vérifie le code 2FA."""
        phone_number = request.data.get("phone_number") # Récupérer le numéro de téléphone du corps de la requête
        serializer = self.get_serializer(data=request.data, context={
            'request': request,
            'phone_number': phone_number # Passer le numéro de téléphone au sérialiseur
        })
        serializer.is_valid(raise_exception=True)        
        code = serializer.validated_data['code']
        
        try:
            two_factor_auth = TwoFactorAuth.objects.get(
                utilisateur=request.user,
                phone_number=phone_number,
                statut='EN_ATTENTE',
                date_expiration__gt=timezone.now()
            )
        except TwoFactorAuth.DoesNotExist:
            return Response({
                'error': 'Aucune configuration 2FA en cours ou expirée'
            }, status=status.HTTP_400_BAD_REQUEST)

        if code != two_factor_auth.verification_code:
            return Response({
                'error': 'Code incorrect'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Activer 2FA pour l\'utilisateur
        user = request.user
        user.telephone = two_factor_auth.phone_number
        user.save()

        # Marquer la 2FA comme vérifiée
        two_factor_auth.statut = 'VERIFIE'
        two_factor_auth.date_verification = timezone.now()
        two_factor_auth.save()

        return Response({
            'message': 'Authentification à deux facteurs activée avec succès'
        }, status=status.HTTP_200_OK)


class PasswordResetRequestView(generics.CreateAPIView):
    """
    Vue pour demander une réinitialisation de mot de passe.
    
    POST /api/auth/password-reset/
    """
    
    serializer_class = PasswordResetRequestSerializer
    permission_classes = [permissions.AllowAny]
    
    def create(self, request, *args, **kwargs):
        """Envoie un email de réinitialisation de mot de passe."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        
        try:
            user = User.objects.get(email=email, is_active=True)
            
            # Générer un token de réinitialisation
            reset_token = secrets.token_urlsafe(32)
            
            # Créer un objet PasswordReset
            password_reset = PasswordReset.objects.create(
                utilisateur=user,
                token=reset_token,
                adresse_ip_creation=self.get_client_ip(request)
            )
            
            # Envoyer l'email
            reset_url = f"{settings.FRONTEND_URL}/reset-password/{reset_token}"
            
            send_mail(
                subject='Réinitialisation de votre mot de passe SpotVibe',
                message=f'''
                Bonjour {user.first_name},
                
                Vous avez demandé la réinitialisation de votre mot de passe.
                
                Cliquez sur le lien suivant pour réinitialiser votre mot de passe :
                {reset_url}
                
                Ce lien expire dans 1 heure.
                
                Si vous n'avez pas demandé cette réinitialisation, ignorez cet email.
                
                L'équipe SpotVibe
                ''',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
            
            return Response({
                'message': 'Email de réinitialisation envoyé'
            }, status=status.HTTP_200_OK)
            
        except User.DoesNotExist:
            # Pour des raisons de sécurité, on retourne le même message
            return Response({
                'message': 'Email de réinitialisation envoyé'
            }, status=status.HTTP_200_OK)


class PasswordResetConfirmView(generics.CreateAPIView):
    """
    Vue pour confirmer la réinitialisation de mot de passe.
    
    POST /api/auth/password-reset/confirm/
    """
    
    serializer_class = PasswordResetConfirmSerializer
    permission_classes = [permissions.AllowAny]
    
    def create(self, request, *args, **kwargs):
        """Confirme la réinitialisation du mot de passe."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        token = serializer.validated_data['token']
        new_password = serializer.validated_data['new_password']
        
        try:
            password_reset = PasswordReset.objects.get(
                token=token,
                statut='ACTIF',
                date_expiration__gt=timezone.now()
            )
        except PasswordReset.DoesNotExist:
            return Response({
                'error': 'Token invalide ou expiré'
            }, status=status.HTTP_400_BAD_REQUEST)

        user = password_reset.utilisateur
        user.set_password(new_password)
        user.save()

        # Marquer le token comme utilisé
        password_reset.statut = 'UTILISE'
        password_reset.date_utilisation = timezone.now()
        password_reset.adresse_ip_utilisation = self.get_client_ip(request)
        password_reset.save()

        return Response({
            'message': 'Mot de passe réinitialisé avec succès'
        }, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def auth_status_view(request):
    """
    Vue pour obtenir le statut d'authentification.
    
    GET /api/auth/status/
    """
    
    user = request.user
    
    # Comptes sociaux connectés
    social_accounts = SocialAccount.objects.filter(
        utilisateur=user,
        actif=True
    ).values('provider', 'email')
    
    # Dernière tentative de connexion
    last_login_attempt = LoginAttempt.objects.filter(
        utilisateur=user,
        reussi=True
    ).order_by('-date_tentative').first()
    
    status_data = {
        'user': UserProfileSerializer(user).data,
        'social_accounts': list(social_accounts),
        'two_factor_enabled': bool(user.telephone),
        'last_login': last_login_attempt.date_tentative if last_login_attempt else None,
        'login_attempts_count': LoginAttempt.objects.filter(
            utilisateur=user,
            date_tentative__gte=timezone.now() - timedelta(days=30)
        ).count()
    }
    
    return Response(status_data, status=status.HTTP_200_OK)

