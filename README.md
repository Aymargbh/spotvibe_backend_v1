# SpotVibe Backend

SpotVibe est une plateforme de découverte d'événements locaux développée avec Django Rest Framework. Cette application permet aux utilisateurs de créer, découvrir et participer à des événements dans leur région.

## 🚀 Fonctionnalités

### 👤 Gestion des utilisateurs
- **Inscription/Connexion** : Système d'authentification complet
- **Profils utilisateurs** : Gestion des informations personnelles
- **Vérification d'identité** : Validation avec documents officiels
- **Système de suivi** : Follow/unfollow entre utilisateurs
- **Authentification sociale** : Google, Facebook (prêt à configurer)

### 📅 Gestion des événements
- **Création d'événements** : Interface complète avec validation admin
- **Catégorisation** : Organisation par catégories personnalisables
- **Géolocalisation** : Intégration Google Maps
- **Recherche avancée** : Filtres par date, lieu, prix, catégorie
- **Participation** : Système de likes et confirmations
- **Partage social** : Partage sur réseaux sociaux

### 💳 Système de paiement
- **Mobile Money** : Intégration complète (Orange Money, MTN, Moov)
- **Billetterie** : Génération de billets avec codes QR
- **Commissions** : Système de commissions automatique
- **Remboursements** : Gestion des demandes de remboursement

### 📊 Abonnements
- **Plans flexibles** : Standard, Premium, Gold
- **Limites personnalisées** : Événements par mois, fonctionnalités
- **Renouvellement automatique** : Gestion des abonnements récurrents

### 🔔 Notifications
- **Multi-canaux** : Email, Push, SMS, In-App
- **Templates personnalisables** : Système de templates flexibles
- **Préférences utilisateur** : Contrôle granulaire des notifications
- **Campagnes** : Envoi en masse avec statistiques

### 👨‍💼 Interface d'administration
- **Dashboard moderne** : Interface Bootstrap responsive
- **Statistiques en temps réel** : Graphiques et métriques
- **Validation de contenu** : Modération des événements et utilisateurs
- **Gestion des paiements** : Suivi des transactions et commissions
- **Audit trail** : Traçabilité complète des actions

## 🛠️ Technologies utilisées

- **Backend** : Django 5.2.4, Django REST Framework
- **Base de données** : SQLite (développement), PostgreSQL (production)
- **Authentification** : Django Auth + OAuth2
- **API** : REST API complète avec documentation
- **Interface Admin** : Django Admin personnalisé avec Bootstrap 5
- **Paiements** : Intégration Mobile Money
- **Notifications** : Système multi-canaux

## 📋 Prérequis

- Python 3.11+
- pip (gestionnaire de paquets Python)
- Git

## 🚀 Installation

1. **Cloner le projet**
```bash
git clone <repository-url>
cd spotvibe_backend
```

2. **Créer un environnement virtuel**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

3. **Installer les dépendances**
```bash
pip install -r requirements.txt
```

4. **Configurer la base de données**
```bash
python manage.py migrate
```

5. **Créer un superutilisateur**
```bash
python manage.py createsuperuser
```

6. **Démarrer le serveur**
```bash
python manage.py runserver
```

L'application sera accessible à l'adresse : http://localhost:8000

## 📚 Documentation API

### Endpoints principaux

#### Authentification
- `POST /api/users/register/` - Inscription
- `POST /api/users/login/` - Connexion
- `POST /api/users/logout/` - Déconnexion
- `GET /api/users/profile/` - Profil utilisateur
- `PUT /api/users/profile/` - Modifier le profil

#### Événements
- `GET /api/events/` - Liste des événements
- `POST /api/events/create/` - Créer un événement
- `GET /api/events/{id}/` - Détails d'un événement
- `PUT /api/events/{id}/update/` - Modifier un événement
- `DELETE /api/events/{id}/delete/` - Supprimer un événement
- `POST /api/events/participate/` - Participer à un événement

#### Recherche et filtres
- `GET /api/events/?search=concert` - Recherche textuelle
- `GET /api/events/?categorie=1` - Filtrer par catégorie
- `GET /api/events/?periode=week` - Événements de la semaine
- `GET /api/events/?prix_max=5000` - Filtrer par prix
- `GET /api/events/?latitude=X&longitude=Y&rayon=10` - Recherche géographique

#### Billetterie
- `POST /api/events/tickets/purchase/` - Acheter un billet
- `GET /api/events/my-tickets/` - Mes billets

### Authentification API

L'API utilise l'authentification par token. Après connexion, incluez le token dans les headers :

```
Authorization: Token your_token_here
```

## 🔧 Configuration

### Variables d'environnement

Créez un fichier `.env` à la racine du projet :

```env
# Base de données
DATABASE_URL=sqlite:///db.sqlite3

# Sécurité
SECRET_KEY=your_secret_key_here
DEBUG=True

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_password

# Mobile Money
ORANGE_MONEY_API_KEY=your_orange_api_key
MTN_MONEY_API_KEY=your_mtn_api_key

# Google Maps
GOOGLE_MAPS_API_KEY=your_google_maps_key

# OAuth Social
GOOGLE_OAUTH2_CLIENT_ID=your_google_client_id
GOOGLE_OAUTH2_CLIENT_SECRET=your_google_client_secret
FACEBOOK_APP_ID=your_facebook_app_id
FACEBOOK_APP_SECRET=your_facebook_app_secret
```

### Configuration Mobile Money

Pour activer les paiements Mobile Money, configurez les clés API dans les settings :

```python
# Orange Money
ORANGE_MONEY_CONFIG = {
    'API_KEY': os.getenv('ORANGE_MONEY_API_KEY'),
    'BASE_URL': 'https://api.orange.com/orange-money-webpay/dev/v1',
    'MERCHANT_KEY': 'your_merchant_key'
}

# MTN Money
MTN_MONEY_CONFIG = {
    'API_KEY': os.getenv('MTN_MONEY_API_KEY'),
    'BASE_URL': 'https://sandbox.momodeveloper.mtn.com',
    'SUBSCRIPTION_KEY': 'your_subscription_key'
}
```

## 👨‍💼 Interface d'administration

Accédez à l'interface d'administration à l'adresse : http://localhost:8000/admin/

### Fonctionnalités admin

- **Dashboard** : Vue d'ensemble avec statistiques
- **Gestion des utilisateurs** : Validation, vérification, modération
- **Validation d'événements** : Approuver/rejeter les événements
- **Gestion des paiements** : Suivi des transactions
- **Système de notifications** : Envoi de notifications
- **Rapports** : Statistiques détaillées

## 🧪 Tests

Exécuter les tests :

```bash
python manage.py test
```

Exécuter les tests avec couverture :

```bash
coverage run --source='.' manage.py test
coverage report
```

## 📱 Intégration mobile

L'API est conçue pour être facilement intégrée avec des applications mobiles :

- **Format JSON** : Toutes les réponses en JSON
- **Pagination** : Pagination automatique des listes
- **Filtres** : Filtres avancés pour toutes les listes
- **Upload d'images** : Support des uploads multipart
- **Géolocalisation** : Endpoints compatibles GPS

## 🔒 Sécurité

- **Authentification** : Token-based authentication
- **Permissions** : Système de permissions granulaire
- **Validation** : Validation stricte des données
- **CORS** : Configuration CORS pour les applications web
- **Rate limiting** : Protection contre les abus (à configurer)

## 📈 Performance

- **Optimisations ORM** : select_related et prefetch_related
- **Cache** : Système de cache Redis (à configurer)
- **Pagination** : Pagination efficace des grandes listes
- **Indexation** : Index de base de données optimisés

## 🚀 Déploiement

### Déploiement sur Heroku

1. Installer Heroku CLI
2. Créer une application Heroku
3. Configurer les variables d'environnement
4. Déployer :

```bash
git add .
git commit -m "Deploy to Heroku"
git push heroku main
heroku run python manage.py migrate
heroku run python manage.py createsuperuser
```

### Déploiement avec Docker

```dockerfile
FROM python:3.11
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
```

## 🤝 Contribution

1. Fork le projet
2. Créer une branche feature (`git checkout -b feature/AmazingFeature`)
3. Commit les changements (`git commit -m 'Add some AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## 📞 Support

Pour toute question ou support :

- **Email** : support@spotvibe.com
- **Documentation** : [docs.spotvibe.com](https://docs.spotvibe.com)
- **Issues** : [GitHub Issues](https://github.com/spotvibe/backend/issues)

## 🎯 Roadmap

### Version 2.0
- [ ] Intégration IA pour recommandations
- [ ] Chat en temps réel
- [ ] Streaming d'événements
- [ ] Application mobile native
- [ ] Système de reviews et ratings

### Version 1.1
- [ ] Notifications push
- [ ] Export de données
- [ ] API GraphQL
- [ ] Système de coupons
- [ ] Multi-langues

---

**SpotVibe** - Découvrez les événements qui vous ressemblent ! 🎉

