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
        
        # Sauvegarder le code temporairement (en production, utilisez Redis)
        request.session['2fa_code'] = verification_code
        request.session['2fa_phone'] = phone_number
        request.session['2fa_expires'] = (
            timezone.now() + timedelta(minutes=5)
        ).isoformat()
        
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
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        code = serializer.validated_data['code']
        
        # Vérifier le code
        session_code = request.session.get('2fa_code')
        session_phone = request.session.get('2fa_phone')
        session_expires = request.session.get('2fa_expires')
        
        if not session_code or not session_phone or not session_expires:
            return Response({
                'error': 'Aucune configuration 2FA en cours'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Vérifier l'expiration
        expires_at = timezone.datetime.fromisoformat(session_expires)
        if timezone.now() > expires_at:
            return Response({
                'error': 'Code expiré. Demandez un nouveau code.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Vérifier le code
        if code != session_code:
            return Response({
                'error': 'Code incorrect'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Activer 2FA pour l'utilisateur
        user = request.user
        user.telephone = session_phone
        user.save()
        
        # Nettoyer la session
        del request.session['2fa_code']
        del request.session['2fa_phone']
        del request.session['2fa_expires']
        
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
            
            # Sauvegarder le token (en production, utilisez Redis ou la DB)
            # Ici, nous simulons avec la session
            request.session[f'reset_token_{reset_token}'] = {
                'user_id': user.id,
                'expires': (timezone.now() + timedelta(hours=1)).isoformat()
            }
            
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
        
        # Vérifier le token
        token_data = request.session.get(f'reset_token_{token}')
        
        if not token_data:
            return Response({
                'error': 'Token invalide ou expiré'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Vérifier l'expiration
        expires_at = timezone.datetime.fromisoformat(token_data['expires'])
        if timezone.now() > expires_at:
            return Response({
                'error': 'Token expiré'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Réinitialiser le mot de passe
        try:
            user = User.objects.get(id=token_data['user_id'])
            user.set_password(new_password)
            user.save()
            
            # Supprimer le token
            del request.session[f'reset_token_{token}']
            
            return Response({
                'message': 'Mot de passe réinitialisé avec succès'
            }, status=status.HTTP_200_OK)
            
        except User.DoesNotExist:
            return Response({
                'error': 'Utilisateur introuvable'
            }, status=status.HTTP_400_BAD_REQUEST)


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

