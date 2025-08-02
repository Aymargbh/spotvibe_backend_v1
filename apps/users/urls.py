"""
URLs pour l'application users.
"""

from django.urls import path
from . import views

urlpatterns = [
    # Authentification
    path('register/', views.UserRegistrationView.as_view(), name='user-register'),
    path('login/', views.UserLoginView.as_view(), name='user-login'),
    path('logout/', views.logout_view, name='user-logout'),
    
    # Profil utilisateur
    path('profile/', views.UserProfileView.as_view(), name='user-profile'),
    path('change-password/', views.PasswordChangeView.as_view(), name='user-change-password'),
    path('stats/', views.user_stats_view, name='user-stats'),
    
    # Vérification d'identité
    path('verification/', views.UserVerificationView.as_view(), name='user-verification'),
    path('verification/status/', views.UserVerificationStatusView.as_view(), name='user-verification-status'),
    
    # Système de suivi
    path('follow/', views.FollowView.as_view(), name='user-follow'),
    path('<int:user_id>/unfollow/', views.unfollow_view, name='user-unfollow'),
    path('<int:user_id>/follow-status/', views.check_follow_status, name='user-follow-status'),
    path('<int:user_id>/followers/', views.UserFollowersView.as_view(), name='user-followers'),
    path('<int:user_id>/following/', views.UserFollowingView.as_view(), name='user-following'),
    
    # Liste et détails des utilisateurs
    path('', views.UserListView.as_view(), name='user-list'),
    path('<int:pk>/', views.UserDetailView.as_view(), name='user-detail'),
]

