"""
URLs pour l'application authentication.
"""

from django.urls import path
from . import views

urlpatterns = [
    # Authentification sociale
    path('google/', views.GoogleAuthView.as_view(), name='auth-google'),
    path('facebook/', views.FacebookAuthView.as_view(), name='auth-facebook'),
    
    # Gestion des comptes sociaux
    path('social-accounts/', views.SocialAccountListView.as_view(), name='social-accounts'),
    path('social-accounts/<str:provider>/disconnect/', views.disconnect_social_account, name='disconnect-social'),
    
    # Authentification à deux facteurs
    path('2fa/setup/', views.TwoFactorSetupView.as_view(), name='2fa-setup'),
    path('2fa/verify/', views.TwoFactorVerifyView.as_view(), name='2fa-verify'),
    
    # Réinitialisation de mot de passe
    path('password-reset/', views.PasswordResetRequestView.as_view(), name='password-reset'),
    path('password-reset/confirm/', views.PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    
    # Historique et statut
    path('login-attempts/', views.LoginAttemptListView.as_view(), name='login-attempts'),
    path('status/', views.auth_status_view, name='auth-status'),
]

