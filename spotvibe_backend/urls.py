"""
Configuration des URLs pour le projet SpotVibe Backend.

Ce fichier définit les routes principales de l'API et inclut les URLs
de toutes les applications. Il gère également les fichiers statiques
et médias en mode développement.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter

# Configuration du routeur principal pour l'API REST
router = DefaultRouter()

from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.urls import re_path

schema_view = get_schema_view(
    openapi.Info(
        title="SpotVibe API",
        default_version='v1',
        description="Documentation interactive de l'API SpotVibe",
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    # Interface d'administration Django
    path('admin/', admin.site.urls),

    # Documentation Swagger et Redoc
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('api/docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

    # APIs des différentes applications
    path('api/auth/', include('apps.authentication.urls')),
    path('api/users/', include('apps.users.urls')),
    path('api/events/', include('apps.events.urls')),
    path('api/subscriptions/', include('apps.subscriptions.urls')),
    path('api/payments/', include('apps.payments.urls')),
    path('api/notifications/', include('apps.notifications.urls')),
    path('api/admin/', include('apps.admin_dashboard.urls')),
    path('api/core/', include('apps.core.urls')),

    # OAuth2
    path('o/', include('oauth2_provider.urls', namespace='oauth2_provider')),

    # API router
    path('api/', include(router.urls)),
]

# Configuration pour servir les fichiers statiques et médias en développement
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Configuration du titre de l'interface d'administration
admin.site.site_header = "SpotVibe Administration"
admin.site.site_title = "SpotVibe Admin"
admin.site.index_title = "Tableau de bord SpotVibe"

