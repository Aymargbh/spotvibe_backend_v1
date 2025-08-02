"""
Vues API pour l'application users.

Ce module définit les vues Django REST Framework pour
la gestion des utilisateurs et de l'authentification.
"""

from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.pagination import PageNumberPagination
from django.contrib.auth import login, logout
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .models import User, UserVerification, Follow
from .serializers import (
    UserRegistrationSerializer, UserLoginSerializer, UserProfileSerializer,
    UserPublicSerializer, UserVerificationSerializer, FollowSerializer,
    FollowCreateSerializer, PasswordChangeSerializer
)


class UserPagination(PageNumberPagination):
    """Pagination personnalisée pour les utilisateurs."""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class UserRegistrationView(generics.CreateAPIView):
    """
    Vue pour l'inscription d'un nouvel utilisateur.
    
    POST /api/users/register/
    """
    
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]
    
    def create(self, request, *args, **kwargs):
        """Crée un nouvel utilisateur et retourne un token."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.save()
        
        # Créer un token pour l'utilisateur
        token, created = Token.objects.get_or_create(user=user)
        
        # Connecter l'utilisateur
        login(request, user)
        
        return Response({
            'message': 'Compte créé avec succès',
            'user': UserProfileSerializer(user).data,
            'token': token.key
        }, status=status.HTTP_201_CREATED)


class UserLoginView(generics.GenericAPIView):
    """
    Vue pour la connexion d'un utilisateur.
    
    POST /api/users/login/
    """
    
    serializer_class = UserLoginSerializer
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, *args, **kwargs):
        """Connecte un utilisateur et retourne un token."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.validated_data['user']
        
        # Créer ou récupérer le token
        token, created = Token.objects.get_or_create(user=user)
        
        # Connecter l'utilisateur
        login(request, user)
        
        return Response({
            'message': 'Connexion réussie',
            'user': UserProfileSerializer(user).data,
            'token': token.key
        }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout_view(request):
    """
    Vue pour la déconnexion d'un utilisateur.
    
    POST /api/users/logout/
    """
    
    # Supprimer le token
    try:
        request.user.auth_token.delete()
    except:
        pass
    
    # Déconnecter l'utilisateur
    logout(request)
    
    return Response({
        'message': 'Déconnexion réussie'
    }, status=status.HTTP_200_OK)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    Vue pour consulter et modifier le profil utilisateur.
    
    GET /api/users/profile/
    PUT /api/users/profile/
    PATCH /api/users/profile/
    """
    
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        """Retourne l'utilisateur connecté."""
        return self.request.user


class UserDetailView(generics.RetrieveAPIView):
    """
    Vue pour consulter le profil public d'un utilisateur.
    
    GET /api/users/{id}/
    """
    
    serializer_class = UserPublicSerializer
    permission_classes = [permissions.AllowAny]
    queryset = User.objects.filter(is_active=True)


class UserListView(generics.ListAPIView):
    """
    Vue pour lister les utilisateurs avec recherche.
    
    GET /api/users/
    """
    
    serializer_class = UserPublicSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = UserPagination
    
    def get_queryset(self):
        """Retourne la liste des utilisateurs avec filtres."""
        queryset = User.objects.filter(is_active=True)
        
        # Recherche par nom ou username
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(username__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )
        
        # Filtrer par utilisateurs vérifiés
        verified = self.request.query_params.get('verified', None)
        if verified == 'true':
            queryset = queryset.filter(est_verifie=True)
        
        return queryset.order_by('-date_creation')


class UserVerificationView(generics.CreateAPIView):
    """
    Vue pour soumettre une demande de vérification.
    
    POST /api/users/verification/
    """
    
    serializer_class = UserVerificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        """Crée une demande de vérification."""
        # Vérifier qu'il n'y a pas déjà une demande en cours
        existing = UserVerification.objects.filter(
            utilisateur=request.user,
            statut='EN_ATTENTE'
        ).first()
        
        if existing:
            return Response({
                'error': 'Vous avez déjà une demande de vérification en cours'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return super().create(request, *args, **kwargs)


class UserVerificationStatusView(generics.RetrieveAPIView):
    """
    Vue pour consulter le statut de vérification.
    
    GET /api/users/verification/status/
    """
    
    serializer_class = UserVerificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        """Retourne la dernière demande de vérification."""
        return get_object_or_404(
            UserVerification,
            utilisateur=self.request.user
        )


class FollowView(generics.CreateAPIView):
    """
    Vue pour suivre un utilisateur.
    
    POST /api/users/follow/
    """
    
    serializer_class = FollowCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        """Crée une relation de suivi."""
        response = super().create(request, *args, **kwargs)
        
        if response.status_code == status.HTTP_201_CREATED:
            return Response({
                'message': 'Utilisateur suivi avec succès'
            }, status=status.HTTP_201_CREATED)
        
        return response


@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def unfollow_view(request, user_id):
    """
    Vue pour ne plus suivre un utilisateur.
    
    DELETE /api/users/{user_id}/unfollow/
    """
    
    try:
        following_user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({
            'error': 'Utilisateur introuvable'
        }, status=status.HTTP_404_NOT_FOUND)
    
    try:
        follow = Follow.objects.get(
            follower=request.user,
            following=following_user
        )
        follow.delete()
        
        return Response({
            'message': 'Vous ne suivez plus cet utilisateur'
        }, status=status.HTTP_200_OK)
        
    except Follow.DoesNotExist:
        return Response({
            'error': 'Vous ne suivez pas cet utilisateur'
        }, status=status.HTTP_400_BAD_REQUEST)


class UserFollowersView(generics.ListAPIView):
    """
    Vue pour lister les followers d'un utilisateur.
    
    GET /api/users/{user_id}/followers/
    """
    
    serializer_class = FollowSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = UserPagination
    
    def get_queryset(self):
        """Retourne les followers de l'utilisateur."""
        user_id = self.kwargs['user_id']
        return Follow.objects.filter(
            following_id=user_id
        ).select_related('follower', 'following').order_by('-date_suivi')


class UserFollowingView(generics.ListAPIView):
    """
    Vue pour lister les utilisateurs suivis.
    
    GET /api/users/{user_id}/following/
    """
    
    serializer_class = FollowSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = UserPagination
    
    def get_queryset(self):
        """Retourne les utilisateurs suivis."""
        user_id = self.kwargs['user_id']
        return Follow.objects.filter(
            follower_id=user_id
        ).select_related('follower', 'following').order_by('-date_suivi')


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def check_follow_status(request, user_id):
    """
    Vue pour vérifier si on suit un utilisateur.
    
    GET /api/users/{user_id}/follow-status/
    """
    
    try:
        following_user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({
            'error': 'Utilisateur introuvable'
        }, status=status.HTTP_404_NOT_FOUND)
    
    is_following = Follow.objects.filter(
        follower=request.user,
        following=following_user
    ).exists()
    
    return Response({
        'is_following': is_following
    }, status=status.HTTP_200_OK)


class PasswordChangeView(generics.GenericAPIView):
    """
    Vue pour changer le mot de passe.
    
    POST /api/users/change-password/
    """
    
    serializer_class = PasswordChangeSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        """Change le mot de passe de l'utilisateur."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        serializer.save()
        
        return Response({
            'message': 'Mot de passe modifié avec succès'
        }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_stats_view(request):
    """
    Vue pour obtenir les statistiques de l'utilisateur.
    
    GET /api/users/stats/
    """
    
    user = request.user
    
    stats = {
        'events_created': user.get_events_count(),
        'events_participated': user.get_participations_count(),
        'followers_count': user.get_followers_count(),
        'following_count': user.get_following_count(),
        'is_verified': user.est_verifie,
        'member_since': user.date_creation.strftime('%Y-%m-%d'),
    }
    
    return Response(stats, status=status.HTTP_200_OK)

