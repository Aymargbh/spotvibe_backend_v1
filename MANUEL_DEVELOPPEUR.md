# Manuel Développeur SpotVibe

Ce manuel technique guide les développeurs dans la compréhension, l'installation, la configuration et l'extension de la plateforme SpotVibe.

## 🏗️ Architecture du système

### Vue d'ensemble

SpotVibe est construit sur une architecture moderne basée sur :

- **Backend** : Django 5.2.4 + Django REST Framework
- **Base de données** : SQLite (dev) / PostgreSQL (prod)
- **API** : REST API avec authentification par token
- **Interface Admin** : Django Admin personnalisé avec Bootstrap 5
- **Cache** : Redis (optionnel)
- **Files d'attente** : Celery + Redis (optionnel)

### Structure du projet

```
spotvibe_backend/
├── spotvibe_backend/          # Configuration principale
│   ├── settings.py           # Paramètres Django
│   ├── urls.py              # URLs principales
│   └── wsgi.py              # Configuration WSGI
├── apps/                    # Applications Django
│   ├── users/              # Gestion des utilisateurs
│   ├── events/             # Gestion des événements
│   ├── payments/           # Système de paiement
│   ├── subscriptions/      # Abonnements
│   ├── notifications/      # Notifications
│   ├── authentication/     # Authentification avancée
│   ├── core/              # Fonctionnalités communes
│   └── admin_dashboard/    # Dashboard admin
├── templates/              # Templates Django
├── static/                # Fichiers statiques
├── media/                 # Fichiers uploadés
└── requirements.txt       # Dépendances Python
```

## 🔧 Installation et configuration

### Prérequis

```bash
# Python 3.11+
python --version

# pip
pip --version

# Git
git --version
```

### Installation locale

```bash
# 1. Cloner le repository
git clone <repository-url>
cd spotvibe_backend

# 2. Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou venv\Scripts\activate  # Windows

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Configuration de base
cp .env.example .env
# Éditer .env avec vos paramètres

# 5. Migrations de base de données
python manage.py migrate

# 6. Créer un superutilisateur
python manage.py createsuperuser

# 7. Collecter les fichiers statiques
python manage.py collectstatic

# 8. Démarrer le serveur
python manage.py runserver
```

### Variables d'environnement

Créez un fichier `.env` :

```env
# Base
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Base de données
DATABASE_URL=sqlite:///db.sqlite3
# ou pour PostgreSQL:
# DATABASE_URL=postgresql://user:password@localhost:5432/spotvibe

# Email
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Mobile Money APIs
ORANGE_MONEY_API_KEY=your-orange-api-key
ORANGE_MONEY_MERCHANT_KEY=your-merchant-key
MTN_MONEY_API_KEY=your-mtn-api-key
MTN_MONEY_SUBSCRIPTION_KEY=your-subscription-key
MOOV_MONEY_API_KEY=your-moov-api-key

# Google Services
GOOGLE_MAPS_API_KEY=your-google-maps-key
GOOGLE_OAUTH2_CLIENT_ID=your-google-client-id
GOOGLE_OAUTH2_CLIENT_SECRET=your-google-client-secret

# Facebook OAuth
FACEBOOK_APP_ID=your-facebook-app-id
FACEBOOK_APP_SECRET=your-facebook-app-secret

# Redis (optionnel)
REDIS_URL=redis://localhost:6379/0

# Celery (optionnel)
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Sentry (monitoring)
SENTRY_DSN=your-sentry-dsn

# AWS S3 (stockage fichiers)
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
AWS_STORAGE_BUCKET_NAME=your-bucket-name
AWS_S3_REGION_NAME=us-east-1
```

## 📊 Modèles de données

### Diagramme ERD

```mermaid
erDiagram
    User ||--o{ Event : creates
    User ||--o{ EventParticipation : participates
    User ||--o{ Follow : follows
    User ||--o{ Payment : makes
    User ||--o{ Subscription : has
    
    Event ||--o{ EventParticipation : has
    Event ||--o{ EventTicket : has
    Event }o--|| EventCategory : belongs_to
    
    Payment ||--o{ EventTicket : for
    Payment ||--o{ Subscription : for
    Payment ||--o{ MomoTransaction : has
    
    SubscriptionPlan ||--o{ Subscription : defines
```

### Modèles principaux

#### User (apps/users/models.py)

```python
class User(AbstractUser):
    """Modèle utilisateur personnalisé."""
    
    # Champs personnalisés
    telephone = models.CharField(max_length=20, unique=True)
    date_naissance = models.DateField(null=True, blank=True)
    photo_profil = models.ImageField(upload_to='profiles/')
    bio = models.TextField(max_length=500, blank=True)
    
    # Vérification
    est_verifie = models.BooleanField(default=False)
    date_verification = models.DateTimeField(null=True, blank=True)
    
    # Préférences
    notifications_email = models.BooleanField(default=True)
    notifications_push = models.BooleanField(default=True)
    
    # Métadonnées
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    derniere_connexion_ip = models.GenericIPAddressField(null=True)
```

#### Event (apps/events/models.py)

```python
class Event(models.Model):
    """Modèle pour les événements."""
    
    STATUT_CHOICES = [
        ('BROUILLON', 'Brouillon'),
        ('EN_ATTENTE', 'En attente de validation'),
        ('VALIDE', 'Validé'),
        ('REJETE', 'Rejeté'),
        ('TERMINE', 'Terminé'),
        ('ANNULE', 'Annulé'),
    ]
    
    # Informations de base
    titre = models.CharField(max_length=200)
    description = models.TextField()
    description_courte = models.CharField(max_length=300)
    
    # Relations
    createur = models.ForeignKey(User, on_delete=models.CASCADE)
    categorie = models.ForeignKey(EventCategory, on_delete=models.CASCADE)
    
    # Date et lieu
    date_debut = models.DateTimeField()
    date_fin = models.DateTimeField()
    lieu = models.CharField(max_length=200)
    adresse = models.TextField()
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    
    # Accès et tarification
    type_acces = models.CharField(max_length=10, choices=TYPE_ACCES_CHOICES)
    prix = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    capacite_max = models.PositiveIntegerField()
    
    # Statut
    statut = models.CharField(max_length=15, choices=STATUT_CHOICES)
    
    # Métadonnées
    date_creation = models.DateTimeField(auto_now_add=True)
    nombre_vues = models.PositiveIntegerField(default=0)
```

## 🔌 API REST

### Architecture API

L'API suit les principes REST avec :

- **Authentification** : Token-based
- **Sérialisation** : Django REST Framework
- **Pagination** : Automatique
- **Filtrage** : django-filter
- **Documentation** : Auto-générée

### Sérialiseurs

#### UserSerializer

```python
class UserProfileSerializer(serializers.ModelSerializer):
    """Sérialiseur pour le profil utilisateur."""
    
    followers_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()
    events_count = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'telephone', 'photo_profil', 'bio', 'est_verifie',
            'followers_count', 'following_count', 'events_count'
        ]
        read_only_fields = ['id', 'username', 'email', 'est_verifie']
    
    def get_followers_count(self, obj):
        return obj.get_followers_count()
```

#### EventSerializer

```python
class EventSerializer(serializers.ModelSerializer):
    """Sérialiseur complet pour les événements."""
    
    createur = UserPublicSerializer(read_only=True)
    categorie = EventCategorySerializer(read_only=True)
    participants_count = serializers.SerializerMethodField()
    is_participating = serializers.SerializerMethodField()
    
    class Meta:
        model = Event
        fields = '__all__'
        read_only_fields = ['id', 'createur', 'statut', 'nombre_vues']
    
    def get_participants_count(self, obj):
        return obj.get_participants_count()
    
    def get_is_participating(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.participations.filter(
                utilisateur=request.user,
                statut='CONFIRME'
            ).exists()
        return False
```

### Vues API

#### ViewSets génériques

```python
class EventViewSet(viewsets.ModelViewSet):
    """ViewSet pour les événements."""
    
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['categorie', 'type_acces', 'createur']
    search_fields = ['titre', 'description', 'lieu']
    ordering_fields = ['date_debut', 'date_creation', 'nombre_vues']
    
    def get_queryset(self):
        return Event.objects.filter(statut='VALIDE').select_related(
            'createur', 'categorie'
        )
    
    def perform_create(self, serializer):
        serializer.save(createur=self.request.user)
```

#### Vues personnalisées

```python
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def participate_event(request, event_id):
    """Participer à un événement."""
    try:
        event = Event.objects.get(id=event_id, statut='VALIDE')
    except Event.DoesNotExist:
        return Response({'error': 'Événement introuvable'}, 
                       status=status.HTTP_404_NOT_FOUND)
    
    participation, created = EventParticipation.objects.get_or_create(
        utilisateur=request.user,
        evenement=event,
        defaults={'statut': 'CONFIRME'}
    )
    
    if created:
        return Response({'message': 'Participation confirmée'})
    else:
        return Response({'message': 'Vous participez déjà à cet événement'})
```

## 💳 Système de paiement

### Architecture des paiements

```python
class PaymentProcessor:
    """Processeur de paiements unifié."""
    
    def __init__(self, provider):
        self.provider = provider
    
    def initiate_payment(self, amount, phone_number, reference):
        """Initie un paiement."""
        if self.provider == 'ORANGE_MONEY':
            return self._orange_money_payment(amount, phone_number, reference)
        elif self.provider == 'MTN_MONEY':
            return self._mtn_money_payment(amount, phone_number, reference)
        elif self.provider == 'MOOV_MONEY':
            return self._moov_money_payment(amount, phone_number, reference)
    
    def _orange_money_payment(self, amount, phone_number, reference):
        """Traitement Orange Money."""
        # Implémentation spécifique Orange Money
        pass
```

### Intégration Mobile Money

#### Orange Money

```python
class OrangeMoneyAPI:
    """Client API Orange Money."""
    
    def __init__(self):
        self.api_key = settings.ORANGE_MONEY_API_KEY
        self.base_url = settings.ORANGE_MONEY_BASE_URL
        self.merchant_key = settings.ORANGE_MONEY_MERCHANT_KEY
    
    def initiate_payment(self, amount, phone_number, order_id):
        """Initie un paiement Orange Money."""
        headers = {
            'Authorization': f'Bearer {self.get_access_token()}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'merchant_key': self.merchant_key,
            'currency': 'XOF',
            'order_id': order_id,
            'amount': amount,
            'return_url': settings.PAYMENT_RETURN_URL,
            'cancel_url': settings.PAYMENT_CANCEL_URL,
            'notif_url': settings.PAYMENT_WEBHOOK_URL,
            'lang': 'fr',
            'reference': f'SPOTVIBE-{order_id}'
        }
        
        response = requests.post(
            f'{self.base_url}/webpayment/v1/transactioninit',
            headers=headers,
            json=data
        )
        
        return response.json()
```

### Webhooks

```python
@csrf_exempt
@api_view(['POST'])
def orange_money_webhook(request):
    """Webhook Orange Money."""
    try:
        data = request.data
        transaction_id = data.get('txnid')
        status = data.get('status')
        
        # Vérifier la signature
        if not verify_orange_signature(request):
            return Response({'error': 'Invalid signature'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        # Traiter la transaction
        transaction = MomoTransaction.objects.get(
            transaction_id=transaction_id
        )
        
        if status == 'SUCCESS':
            transaction.payment.statut = 'REUSSI'
            transaction.payment.save()
            
            # Traitement post-paiement
            process_successful_payment(transaction.payment)
        
        return Response({'status': 'OK'})
        
    except Exception as e:
        logger.error(f'Webhook error: {e}')
        return Response({'error': 'Processing error'}, 
                       status=status.HTTP_500_INTERNAL_SERVER_ERROR)
```

## 🔔 Système de notifications

### Architecture

```python
class NotificationService:
    """Service de notifications unifié."""
    
    def send_notification(self, user, notification_type, context=None):
        """Envoie une notification multi-canaux."""
        template = NotificationTemplate.objects.get(
            type_notification=notification_type,
            actif=True
        )
        
        # Créer la notification
        notification = Notification.objects.create(
            utilisateur=user,
            type_notification=notification_type,
            titre=self.render_template(template.titre_push, context),
            message=self.render_template(template.contenu_push, context)
        )
        
        # Envoyer selon les préférences
        preferences = user.notification_preferences.filter(
            type_notification=notification_type,
            actif=True
        )
        
        for pref in preferences:
            if pref.canal == 'EMAIL':
                self.send_email(user, template, context)
            elif pref.canal == 'PUSH':
                self.send_push(user, template, context)
            elif pref.canal == 'SMS':
                self.send_sms(user, template, context)
```

### Notifications Push

```python
class PushNotificationService:
    """Service de notifications push."""
    
    def send_push_notification(self, user, title, message, data=None):
        """Envoie une notification push."""
        tokens = PushToken.objects.filter(
            utilisateur=user,
            actif=True
        )
        
        for token in tokens:
            try:
                if token.plateforme == 'ANDROID':
                    self.send_fcm_notification(token.token, title, message, data)
                elif token.plateforme == 'IOS':
                    self.send_apns_notification(token.token, title, message, data)
                    
                # Mettre à jour les statistiques
                token.notifications_envoyees += 1
                token.save()
                
            except Exception as e:
                logger.error(f'Push notification error: {e}')
                # Marquer le token comme inactif si erreur persistante
                if 'invalid token' in str(e).lower():
                    token.actif = False
                    token.save()
```

## 🎨 Interface d'administration

### Personnalisation Django Admin

#### Configuration de base

```python
# apps/admin_dashboard/admin.py
from django.contrib import admin
from django.utils.html import format_html

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    """Interface admin pour les événements."""
    
    list_display = [
        'titre', 'createur', 'categorie', 'date_debut', 
        'statut', 'get_participants_count', 'get_revenue'
    ]
    
    list_filter = [
        'statut', 'categorie', 'type_acces', 'date_creation'
    ]
    
    search_fields = ['titre', 'description', 'lieu']
    
    actions = ['approve_events', 'reject_events']
    
    def get_participants_count(self, obj):
        count = obj.get_participants_count()
        return format_html('<strong>{}</strong>', count)
    get_participants_count.short_description = 'Participants'
    
    def approve_events(self, request, queryset):
        updated = queryset.update(statut='VALIDE')
        self.message_user(request, f'{updated} événements approuvés.')
    approve_events.short_description = 'Approuver les événements'
```

#### Templates personnalisés

```html
<!-- templates/admin/base_site.html -->
{% extends "admin/base.html" %}
{% load static %}

{% block title %}{{ title }} | SpotVibe Administration{% endblock %}

{% block branding %}
<h1 id="site-name">
    <a href="{% url 'admin:index' %}">
        <i class="fas fa-calendar-alt"></i>
        SpotVibe Administration
    </a>
</h1>
{% endblock %}

{% block extrastyle %}
{{ block.super }}
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
<link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
<style>
    /* Styles personnalisés */
    #header { background: linear-gradient(135deg, #007bff, #0056b3); }
    .module { border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
</style>
{% endblock %}
```

### Dashboard personnalisé

```python
# apps/admin_dashboard/views.py
class AdminDashboardView(TemplateView):
    """Vue du dashboard administrateur."""
    
    template_name = 'admin/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Statistiques générales
        context.update({
            'total_users': User.objects.count(),
            'total_events': Event.objects.filter(statut='VALIDE').count(),
            'pending_events': Event.objects.filter(statut='EN_ATTENTE').count(),
            'total_revenue': Payment.objects.filter(
                statut='REUSSI'
            ).aggregate(Sum('montant'))['montant__sum'] or 0,
            
            # Données pour graphiques
            'events_stats': self.get_events_stats(),
            'revenue_data': self.get_revenue_data(),
            
            # Listes récentes
            'recent_events': Event.objects.filter(
                statut='EN_ATTENTE'
            ).order_by('-date_creation')[:10],
            'recent_users': User.objects.order_by('-date_creation')[:10],
        })
        
        return context
    
    def get_events_stats(self):
        """Statistiques des événements par statut."""
        return Event.objects.values('statut').annotate(
            count=Count('id')
        )
```

## 🧪 Tests

### Structure des tests

```python
# apps/users/tests.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status

User = get_user_model()

class UserModelTest(TestCase):
    """Tests du modèle User."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            telephone='+2250123456789'
        )
    
    def test_user_creation(self):
        """Test de création d'utilisateur."""
        self.assertEqual(self.user.username, 'testuser')
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertTrue(self.user.check_password('testpass123'))
    
    def test_user_str_representation(self):
        """Test de la représentation string."""
        self.assertEqual(str(self.user), 'testuser')

class UserAPITest(APITestCase):
    """Tests de l'API utilisateurs."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            telephone='+2250123456789'
        )
    
    def test_user_registration(self):
        """Test d'inscription utilisateur."""
        data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'newpass123',
            'password_confirm': 'newpass123',
            'first_name': 'New',
            'last_name': 'User',
            'telephone': '+2250987654321'
        }
        
        response = self.client.post('/api/users/register/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('token', response.data)
    
    def test_user_login(self):
        """Test de connexion utilisateur."""
        data = {
            'login': 'test@example.com',
            'password': 'testpass123'
        }
        
        response = self.client.post('/api/users/login/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
```

### Tests d'intégration

```python
class EventIntegrationTest(APITestCase):
    """Tests d'intégration pour les événements."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='organizer',
            email='organizer@example.com',
            password='pass123',
            telephone='+2250123456789'
        )
        
        self.category = EventCategory.objects.create(
            nom='Test Category',
            description='Test description'
        )
        
        self.client.force_authenticate(user=self.user)
    
    def test_event_creation_workflow(self):
        """Test du workflow complet de création d'événement."""
        # 1. Créer un événement
        event_data = {
            'titre': 'Test Event',
            'description': 'Test description',
            'description_courte': 'Short desc',
            'categorie': self.category.id,
            'date_debut': '2024-12-25T20:00:00Z',
            'date_fin': '2024-12-25T23:00:00Z',
            'lieu': 'Test Venue',
            'adresse': 'Test Address',
            'type_acces': 'GRATUIT',
            'prix': 0,
            'capacite_max': 100
        }
        
        response = self.client.post('/api/events/create/', event_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        event_id = response.data['event']['id']
        
        # 2. Vérifier que l'événement est en attente
        event = Event.objects.get(id=event_id)
        self.assertEqual(event.statut, 'EN_ATTENTE')
        
        # 3. Valider l'événement (admin)
        admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123',
            telephone='+2250999999999'
        )
        
        event.statut = 'VALIDE'
        event.validateur = admin_user
        event.save()
        
        # 4. Participer à l'événement
        participant = User.objects.create_user(
            username='participant',
            email='participant@example.com',
            password='pass123',
            telephone='+2250888888888'
        )
        
        self.client.force_authenticate(user=participant)
        
        response = self.client.post('/api/events/participate/', {
            'event_id': event_id,
            'statut': 'CONFIRME'
        })
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # 5. Vérifier la participation
        participation = EventParticipation.objects.get(
            utilisateur=participant,
            evenement=event
        )
        self.assertEqual(participation.statut, 'CONFIRME')
```

### Commandes de test

```bash
# Tous les tests
python manage.py test

# Tests spécifiques
python manage.py test apps.users.tests
python manage.py test apps.events.tests.EventAPITest

# Avec couverture
coverage run --source='.' manage.py test
coverage report
coverage html  # Génère un rapport HTML
```

## 🚀 Déploiement

### Configuration de production

```python
# settings/production.py
from .base import *
import os

DEBUG = False
ALLOWED_HOSTS = ['api.spotvibe.com', 'spotvibe.com']

# Base de données
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}

# Cache Redis
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.getenv('REDIS_URL'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Stockage S3
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
STATICFILES_STORAGE = 'storages.backends.s3boto3.S3StaticStorage'

AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME')

# Sécurité
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
```

### Docker

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Dépendances système
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Code source
COPY . .

# Variables d'environnement
ENV PYTHONPATH=/app
ENV DJANGO_SETTINGS_MODULE=spotvibe_backend.settings.production

# Port
EXPOSE 8000

# Commande de démarrage
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "spotvibe_backend.wsgi:application"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DEBUG=False
      - DATABASE_URL=postgresql://postgres:password@db:5432/spotvibe
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    volumes:
      - ./media:/app/media

  db:
    image: postgres:13
    environment:
      POSTGRES_DB: spotvibe
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:6-alpine
    volumes:
      - redis_data:/data

  celery:
    build: .
    command: celery -A spotvibe_backend worker -l info
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/spotvibe
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis

volumes:
  postgres_data:
  redis_data:
```

### Déploiement Heroku

```bash
# Procfile
web: gunicorn spotvibe_backend.wsgi:application
worker: celery -A spotvibe_backend worker -l info
beat: celery -A spotvibe_backend beat -l info
```

```bash
# Commandes de déploiement
heroku create spotvibe-api
heroku addons:create heroku-postgresql:hobby-dev
heroku addons:create heroku-redis:hobby-dev

# Variables d'environnement
heroku config:set SECRET_KEY=your-secret-key
heroku config:set DJANGO_SETTINGS_MODULE=spotvibe_backend.settings.production

# Déploiement
git push heroku main
heroku run python manage.py migrate
heroku run python manage.py createsuperuser
```

## 🔧 Maintenance et monitoring

### Logging

```python
# settings/base.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/django.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'spotvibe_backend': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}
```

### Monitoring avec Sentry

```python
# settings/production.py
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.celery import CeleryIntegration

sentry_sdk.init(
    dsn=os.getenv('SENTRY_DSN'),
    integrations=[
        DjangoIntegration(auto_enabling=True),
        CeleryIntegration(auto_enabling=True),
    ],
    traces_sample_rate=0.1,
    send_default_pii=True
)
```

### Commandes de maintenance

```python
# management/commands/cleanup_old_data.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

class Command(BaseCommand):
    help = 'Nettoie les anciennes données'
    
    def handle(self, *args, **options):
        # Supprimer les anciens tokens expirés
        cutoff_date = timezone.now() - timedelta(days=30)
        
        # Supprimer les anciennes tentatives de connexion
        LoginAttempt.objects.filter(
            date_tentative__lt=cutoff_date
        ).delete()
        
        # Supprimer les anciens logs d'audit
        AuditLog.objects.filter(
            date_action__lt=cutoff_date
        ).delete()
        
        self.stdout.write(
            self.style.SUCCESS('Nettoyage terminé avec succès')
        )
```

## 📈 Performance et optimisation

### Optimisations de base de données

```python
# Utilisation de select_related et prefetch_related
def get_events_optimized():
    return Event.objects.select_related(
        'createur', 'categorie', 'validateur'
    ).prefetch_related(
        'participations__utilisateur',
        'tickets'
    ).filter(statut='VALIDE')

# Index de base de données
class Event(models.Model):
    # ...
    class Meta:
        indexes = [
            models.Index(fields=['statut', 'date_debut']),
            models.Index(fields=['createur', 'statut']),
            models.Index(fields=['categorie', 'statut']),
        ]
```

### Cache

```python
from django.core.cache import cache
from django.views.decorators.cache import cache_page

@cache_page(60 * 15)  # Cache 15 minutes
def event_list_view(request):
    # Vue mise en cache
    pass

# Cache manuel
def get_event_stats():
    cache_key = 'event_stats'
    stats = cache.get(cache_key)
    
    if stats is None:
        stats = {
            'total_events': Event.objects.filter(statut='VALIDE').count(),
            'total_participants': EventParticipation.objects.count(),
        }
        cache.set(cache_key, stats, 60 * 30)  # 30 minutes
    
    return stats
```

### Pagination optimisée

```python
class OptimizedPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
    
    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data,
            'page_info': {
                'current_page': self.page.number,
                'total_pages': self.page.paginator.num_pages,
                'page_size': self.page_size
            }
        })
```

## 🔒 Sécurité

### Authentification et autorisation

```python
from rest_framework.permissions import BasePermission

class IsOwnerOrReadOnly(BasePermission):
    """Permission personnalisée pour les propriétaires."""
    
    def has_object_permission(self, request, view, obj):
        # Lecture pour tous
        if request.method in SAFE_METHODS:
            return True
        
        # Écriture pour le propriétaire uniquement
        return obj.createur == request.user

class IsVerifiedUser(BasePermission):
    """Permission pour les utilisateurs vérifiés."""
    
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.est_verifie
        )
```

### Validation des données

```python
from django.core.validators import RegexValidator

class PhoneNumberValidator(RegexValidator):
    regex = r'^\+225[0-9]{8,10}$'
    message = 'Numéro de téléphone invalide. Format: +225XXXXXXXX'

# Dans les modèles
telephone = models.CharField(
    max_length=20,
    validators=[PhoneNumberValidator()]
)
```

### Rate limiting

```python
from django_ratelimit.decorators import ratelimit

@ratelimit(key='ip', rate='5/m', method='POST')
def login_view(request):
    # Limite les tentatives de connexion
    pass

@ratelimit(key='user', rate='100/h')
def api_view(request):
    # Limite les requêtes par utilisateur
    pass
```

## 📚 Documentation et bonnes pratiques

### Documentation du code

```python
class EventService:
    """
    Service pour la gestion des événements.
    
    Ce service centralise la logique métier liée aux événements,
    incluant la création, validation, et gestion des participations.
    """
    
    def create_event(self, user, event_data):
        """
        Crée un nouvel événement.
        
        Args:
            user (User): Utilisateur créateur
            event_data (dict): Données de l'événement
            
        Returns:
            Event: L'événement créé
            
        Raises:
            ValidationError: Si les données sont invalides
            PermissionError: Si l'utilisateur n'a pas les droits
        """
        # Vérifier les permissions
        if not self._can_create_event(user):
            raise PermissionError("Droits insuffisants")
        
        # Valider les données
        serializer = EventCreateSerializer(data=event_data)
        serializer.is_valid(raise_exception=True)
        
        # Créer l'événement
        event = serializer.save(createur=user)
        
        # Notifications
        self._notify_admin_new_event(event)
        
        return event
```

### Tests de documentation

```python
def test_api_documentation():
    """Teste que la documentation API est accessible."""
    response = client.get('/api/docs/')
    assert response.status_code == 200
    assert 'SpotVibe API' in response.content.decode()
```

---

Ce manuel développeur fournit une base solide pour comprendre, maintenir et étendre la plateforme SpotVibe. Pour toute question technique, consultez la documentation en ligne ou contactez l'équipe de développement.

**Contact technique :** dev@spotvibe.com  
**Repository :** https://github.com/spotvibe/backend  
**Documentation :** https://docs.spotvibe.com

