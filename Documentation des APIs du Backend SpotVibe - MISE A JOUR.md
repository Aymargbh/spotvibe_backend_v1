# Documentation des APIs du Backend SpotVibe - VERSION MISE À JOUR

Ce document fournit une documentation complète et mise à jour des APIs exposées par le backend de SpotVibe. Il inclut toutes les nouvelles fonctionnalités ajoutées et les corrections apportées au système.

## Table des Matières

1. [Application `authentication`](#1-application-authentication)
2. [Application `users`](#2-application-users)
3. [Application `events`](#3-application-events)
4. [Application `notifications`](#4-application-notifications)
5. [Application `subscriptions`](#5-application-subscriptions)
6. [Application `payments`](#6-application-payments)
7. [Application `admin_dashboard`](#7-application-admin_dashboard)
8. [Application `core`](#8-application-core)

---

## 1. Application `authentication`

L'application `authentication` gère tout ce qui concerne l'authentification des utilisateurs, y compris l'authentification sociale, la gestion des mots de passe, l'authentification à deux facteurs et le suivi des tentatives de connexion.

### 1.1. Authentification Sociale

#### `POST /api/auth/google/`

**Description:** Authentifie un utilisateur via Google OAuth2.

**Corps de la requête (JSON):**
```json
{
  "access_token": "<token_d_acces_google>"
}
```

**Réponses (JSON):**
- **200 OK:** Authentification réussie
  ```json
  {
    "access": "<jwt_access_token>",
    "refresh": "<jwt_refresh_token>",
    "user": {
      "id": 1,
      "username": "utilisateur_google",
      "email": "utilisateur@gmail.com",
      "first_name": "Nom",
      "last_name": "Prénom",
      "photo_profil": "/media/profiles/photo.jpg",
      "est_verifie": false
    }
  }
  ```

#### `POST /api/auth/facebook/`

**Description:** Authentifie un utilisateur via Facebook OAuth2.

**Corps de la requête (JSON):**
```json
{
  "access_token": "<token_d_acces_facebook>"
}
```

### 1.2. Gestion des Comptes Sociaux

#### `GET /api/auth/social-accounts/`

**Description:** Récupère la liste des comptes sociaux liés à l'utilisateur authentifié.

#### `POST /api/auth/social-accounts/<str:provider>/disconnect/`

**Description:** Déconnecte un compte social spécifique.

### 1.3. Authentification à Deux Facteurs (2FA)

#### `POST /api/auth/2fa/setup/`

**Description:** Initialise la configuration de l'authentification à deux facteurs.

#### `POST /api/auth/2fa/verify/`

**Description:** Vérifie le code 2FA fourni par l'utilisateur.

### 1.4. Réinitialisation de Mot de Passe

#### `POST /api/auth/password-reset/`

**Description:** Demande une réinitialisation de mot de passe.

#### `POST /api/auth/password-reset/confirm/`

**Description:** Confirme la réinitialisation du mot de passe.

### 1.5. Historique et Statut

#### `GET /api/auth/login-attempts/`

**Description:** Récupère l'historique des tentatives de connexion.

#### `GET /api/auth/status/`

**Description:** Vérifie le statut d'authentification de l'utilisateur.

---

## 2. Application `users`

L'application `users` gère la création, la gestion et l'interaction avec les profils utilisateurs.

### 2.1. Authentification et Gestion de Compte

#### `POST /api/users/register/`

**Description:** Enregistre un nouvel utilisateur.

**Corps de la requête (JSON):**
```json
{
  "username": "nouvel_utilisateur",
  "email": "nouvel_utilisateur@example.com",
  "password": "mot_de_passe_securise",
  "password_confirm": "mot_de_passe_securise",
  "telephone": "+22997000000",
  "first_name": "Nom",
  "last_name": "Prénom",
  "date_naissance": "1990-01-01"
}
```

**Réponses (JSON):**
- **201 Created:** Utilisateur enregistré avec succès
  ```json
  {
    "message": "Compte créé avec succès",
    "user": {
      "id": 2,
      "username": "nouvel_utilisateur",
      "email": "nouvel_utilisateur@example.com",
      "first_name": "Nom",
      "last_name": "Prénom"
    },
    "token": "<auth_token>"
  }
  ```

#### `POST /api/users/login/`

**Description:** Connecte un utilisateur.

**Corps de la requête (JSON):**
```json
{
  "login": "utilisateur@example.com",
  "password": "mot_de_passe"
}
```

**Réponses (JSON):**
- **200 OK:** Connexion réussie
  ```json
  {
    "message": "Connexion réussie",
    "user": { /* détails utilisateur */ },
    "token": "<auth_token>"
  }
  ```

#### `POST /api/users/logout/`

**Description:** Déconnecte l'utilisateur.

### 2.2. Profil Utilisateur

#### `GET /api/users/profile/`

**Description:** Récupère le profil de l'utilisateur authentifié.

#### `PUT /api/users/profile/`

**Description:** Met à jour le profil de l'utilisateur.

#### `POST /api/users/change-password/`

**Description:** Change le mot de passe de l'utilisateur.

#### `GET /api/users/stats/`

**Description:** Récupère les statistiques de l'utilisateur.

### 2.3. Vérification d'Identité

#### `POST /api/users/verification/`

**Description:** Soumet une demande de vérification d'identité.

#### `GET /api/users/verification/status/`

**Description:** Récupère le statut de vérification.

### 2.4. Système de Suivi

#### `POST /api/users/follow/`

**Description:** Suit un autre utilisateur.

#### `DELETE /api/users/<int:user_id>/unfollow/`

**Description:** Ne plus suivre un utilisateur.

#### `GET /api/users/<int:user_id>/follow-status/`

**Description:** Vérifie le statut de suivi.

#### `GET /api/users/<int:user_id>/followers/`

**Description:** Liste des followers d'un utilisateur.

#### `GET /api/users/<int:user_id>/following/`

**Description:** Liste des utilisateurs suivis.

### 2.5. Liste et Détails

#### `GET /api/users/`

**Description:** Liste tous les utilisateurs avec recherche.

**Paramètres de requête:**
- `search`: Terme de recherche
- `verified`: Filtrer par utilisateurs vérifiés

#### `GET /api/users/<int:pk>/`

**Description:** Détails d'un utilisateur spécifique.

---

## 3. Application `events`

L'application `events` gère tous les aspects des événements, de leur création à leur gestion complète.

### 3.1. Catégories d'Événements

#### `GET /api/events/categories/`

**Description:** Liste toutes les catégories d'événements actives.

**Réponses (JSON):**
- **200 OK:** Liste des catégories
  ```json
  [
    {
      "id": 1,
      "nom": "Mariage",
      "description": "Événements de mariage",
      "icone": "fas fa-heart",
      "couleur": "#ff69b4",
      "ordre": 1,
      "actif": true
    }
  ]
  ```

### 3.2. CRUD Événements

#### `GET /api/events/`

**Description:** Liste tous les événements avec pagination et filtres.

**Paramètres de requête:**
- `category`: ID de la catégorie
- `status`: Statut de l'événement
- `search`: Terme de recherche
- `ordering`: Tri des résultats

#### `POST /api/events/create/`

**Description:** Crée un nouvel événement.

**Corps de la requête (JSON):**
```json
{
  "titre": "Mon Événement",
  "description": "Description détaillée",
  "description_courte": "Résumé court",
  "date_debut": "2024-12-01T18:00:00Z",
  "date_fin": "2024-12-01T23:00:00Z",
  "lieu": "Centre de Conférences",
  "adresse": "123 Rue de l'Événement, Cotonou",
  "latitude": 6.3703,
  "longitude": 2.3912,
  "categorie": 1,
  "type_acces": "PAYANT",
  "prix": 5000,
  "capacite_max": 200,
  "billetterie_activee": true
}
```

#### `GET /api/events/<int:pk>/`

**Description:** Détails d'un événement spécifique.

#### `PUT /api/events/<int:pk>/update/`

**Description:** Met à jour un événement.

#### `DELETE /api/events/<int:pk>/delete/`

**Description:** Supprime un événement.

### 3.3. Gestion des Médias

#### `GET /api/events/<int:event_id>/medias/`

**Description:** Liste les médias d'un événement.

**Paramètres de requête:**
- `type`: Type de média (`image` ou `video`)
- `usage`: Usage du média (`galerie`, `couverture`, `post_cover`)

#### `POST /api/events/<int:event_id>/medias/upload/`

**Description:** Upload un nouveau média vers un événement.

**Corps de la requête (Multipart Form Data):**
- `fichier`: Le fichier à uploader
- `type_media`: Type (`image` ou `video`)
- `usage`: Usage (`galerie`, `couverture`, `post_cover`)
- `titre`: Titre du média (optionnel)
- `description`: Description (optionnel)

#### `GET /api/events/medias/<int:pk>/`

**Description:** Détails d'un média spécifique.

#### `DELETE /api/events/medias/<int:pk>/delete/`

**Description:** Supprime définitivement un média.

#### `POST /api/events/<int:event_id>/set-cover/<int:media_id>/`

**Description:** Définit l'image de couverture principale.

#### `POST /api/events/<int:event_id>/set-post-cover/<int:media_id>/`

**Description:** Définit l'image de couverture pour les posts.

### 3.4. Participations

#### `POST /api/events/participate/`

**Description:** Participe à un événement.

**Corps de la requête (JSON):**
```json
{
  "event_id": 1,
  "statut": "PARTICIPE"
}
```

#### `DELETE /api/events/<int:event_id>/cancel-participation/`

**Description:** Annule la participation à un événement.

#### `GET /api/events/<int:event_id>/participants/`

**Description:** Liste les participants d'un événement.

### 3.5. Partages

#### `POST /api/events/share/`

**Description:** Partage un événement sur une plateforme.

**Corps de la requête (JSON):**
```json
{
  "event_id": 1,
  "plateforme": "FACEBOOK"
}
```

#### `POST /api/events/shares/<int:pk>/click/`

**Description:** Enregistre un clic sur un lien partagé.

### 3.6. Billetterie

#### `POST /api/events/tickets/purchase/`

**Description:** Achète des billets pour un événement.

**Corps de la requête (JSON):**
```json
{
  "event_id": 1,
  "nom": "Billet Standard",
  "prix": 5000,
  "quantite": 2,
  "description": "Accès standard à l'événement"
}
```

#### `GET /api/events/tickets/<uuid:uuid>/`

**Description:** Détails d'un billet spécifique.

#### `POST /api/events/tickets/<uuid:uuid>/validate/`

**Description:** Valide un billet à l'entrée.

#### `GET /api/events/<int:event_id>/tickets/`

**Description:** Liste les billets d'un événement.

### 3.7. Événements Utilisateur

#### `GET /api/events/my-events/`

**Description:** Liste les événements créés par l'utilisateur.

#### `GET /api/events/my-participations/`

**Description:** Liste les participations de l'utilisateur.

#### `GET /api/events/my-tickets/`

**Description:** Liste les billets de l'utilisateur.

### 3.8. Recherche et Recommandations

#### `GET /api/events/search/`

**Description:** Recherche avancée d'événements.

**Paramètres de requête:**
- `q`: Terme de recherche
- `category`: ID de catégorie
- `location`: Localisation
- `date_from`: Date de début
- `date_to`: Date de fin
- `prix_min`: Prix minimum
- `prix_max`: Prix maximum
- `type_acces`: Type d'accès
- `sort`: Tri des résultats

#### `GET /api/events/nearby/`

**Description:** Trouve les événements à proximité.

**Paramètres de requête:**
- `lat`: Latitude
- `lng`: Longitude
- `radius`: Rayon en km (défaut: 10)

#### `GET /api/events/recommendations/`

**Description:** Recommandations personnalisées d'événements.

### 3.9. Statistiques et Tendances

#### `GET /api/events/stats/`

**Description:** Statistiques générales des événements.

#### `GET /api/events/trending/`

**Description:** Événements tendance.

#### `GET /api/events/<int:event_id>/analytics/`

**Description:** Analytics détaillées d'un événement.

### 3.10. Actions Administratives

#### `POST /api/events/<int:event_id>/approve/`

**Description:** Approuve un événement (admin uniquement).

#### `POST /api/events/<int:event_id>/reject/`

**Description:** Rejette un événement (admin uniquement).

#### `GET /api/events/pending-approval/`

**Description:** Liste les événements en attente de validation.

### 3.11. Export et Rapports

#### `GET /api/events/<int:event_id>/export-participants/`

**Description:** Exporte la liste des participants en CSV.

#### `GET /api/events/<int:event_id>/generate-report/`

**Description:** Génère un rapport détaillé de l'événement.

---

## 4. Application `notifications`

L'application `notifications` gère le système de notifications de la plateforme.

### 4.1. Gestion des Notifications

#### `GET /api/notifications/`

**Description:** Liste les notifications de l'utilisateur.

**Paramètres de requête:**
- `statut`: Filtrer par statut (`NOUVEAU`, `LU`)
- `type`: Filtrer par type de notification

#### `GET /api/notifications/<int:pk>/`

**Description:** Détails d'une notification (marque automatiquement comme lue).

#### `POST /api/notifications/mark-read/`

**Description:** Marque des notifications comme lues.

**Corps de la requête (JSON):**
```json
{
  "notification_ids": [1, 2, 3]
}
```

#### `POST /api/notifications/mark-all-read/`

**Description:** Marque toutes les notifications comme lues.

#### `GET /api/notifications/unread-count/`

**Description:** Nombre de notifications non lues.

#### `DELETE /api/notifications/<int:notification_id>/delete/`

**Description:** Supprime une notification.

### 4.2. Statistiques et Préférences

#### `GET /api/notifications/stats/`

**Description:** Statistiques des notifications.

#### `GET /api/notifications/preferences/`

**Description:** Préférences de notifications de l'utilisateur.

#### `PUT /api/notifications/preferences/`

**Description:** Met à jour les préférences de notifications.

### 4.3. Push Tokens et Templates

#### `GET /api/notifications/push-tokens/`

**Description:** Liste les tokens push de l'utilisateur.

#### `POST /api/notifications/push-tokens/`

**Description:** Enregistre un nouveau token push.

#### `GET /api/notifications/templates/`

**Description:** Liste les templates de notifications.

### 4.4. Actions Administratives

#### `POST /api/notifications/bulk-send/`

**Description:** Envoie des notifications en masse (admin uniquement).

#### `POST /api/notifications/test/`

**Description:** Envoie une notification de test.

---

## 5. Application `subscriptions`

L'application `subscriptions` gère le système d'abonnements premium.

### 5.1. Plans d'Abonnement

#### `GET /api/subscriptions/plans/`

**Description:** Liste tous les plans d'abonnement disponibles.

**Réponses (JSON):**
- **200 OK:** Liste des plans
  ```json
  [
    {
      "id": 1,
      "nom": "Standard",
      "type_plan": "STANDARD",
      "prix": 10000,
      "duree": "MENSUEL",
      "description": "Plan standard avec fonctionnalités de base",
      "max_evenements_par_mois": 5,
      "commission_reduite": 8.0,
      "support_prioritaire": false,
      "analytics_avances": false,
      "promotion_evenements": false,
      "personnalisation_profil": false
    }
  ]
  ```

#### `GET /api/subscriptions/plans/<int:pk>/`

**Description:** Détails d'un plan d'abonnement.

#### `GET /api/subscriptions/compare/`

**Description:** Compare tous les plans d'abonnement.

### 5.2. Gestion des Abonnements

#### `GET /api/subscriptions/`

**Description:** Liste les abonnements de l'utilisateur.

#### `GET /api/subscriptions/<int:pk>/`

**Description:** Détails d'un abonnement.

#### `GET /api/subscriptions/current/`

**Description:** Abonnement actuel de l'utilisateur.

### 5.3. Actions sur les Abonnements

#### `POST /api/subscriptions/renew/`

**Description:** Renouvelle un abonnement.

#### `POST /api/subscriptions/cancel/`

**Description:** Annule un abonnement.

#### `POST /api/subscriptions/upgrade/`

**Description:** Change de plan d'abonnement.

**Corps de la requête (JSON):**
```json
{
  "plan_id": 2
}
```

#### `POST /api/subscriptions/pay/`

**Description:** Initie le paiement d'un abonnement.

**Corps de la requête (JSON):**
```json
{
  "subscription_id": 1,
  "payment_method": "MTN_MONEY",
  "phone_number": "+22997000000"
}
```

### 5.4. Informations et Statistiques

#### `GET /api/subscriptions/usage/`

**Description:** Utilisation de l'abonnement actuel.

#### `GET /api/subscriptions/benefits/`

**Description:** Avantages de l'abonnement actuel.

#### `GET /api/subscriptions/history/`

**Description:** Historique des abonnements.

#### `GET /api/subscriptions/stats/`

**Description:** Statistiques d'abonnement.

### 5.5. Webhooks

#### `POST /api/subscriptions/activate-webhook/`

**Description:** Webhook pour activer un abonnement après paiement.

---

## 6. Application `payments`

L'application `payments` gère tous les aspects des paiements et transactions.

### 6.1. Gestion des Paiements

#### `GET /api/payments/`

**Description:** Liste les paiements de l'utilisateur.

#### `POST /api/payments/initiate/`

**Description:** Initie un nouveau paiement.

**Corps de la requête (JSON):**
```json
{
  "type_paiement": "BILLET",
  "montant": 5000,
  "methode_paiement": "MTN_MONEY",
  "telephone_paiement": "+22997000000",
  "description": "Achat de billet pour événement"
}
```

#### `GET /api/payments/<uuid:uuid>/`

**Description:** Détails d'un paiement.

#### `POST /api/payments/verify/`

**Description:** Vérifie le statut d'un paiement.

#### `POST /api/payments/cancel/`

**Description:** Annule un paiement.

#### `POST /api/payments/retry/`

**Description:** Relance un paiement échoué.

### 6.2. Remboursements

#### `GET /api/payments/refunds/`

**Description:** Liste les remboursements.

#### `GET /api/payments/refunds/<int:pk>/`

**Description:** Détails d'un remboursement.

### 6.3. Statistiques et Informations

#### `GET /api/payments/stats/`

**Description:** Statistiques de paiement.

#### `GET /api/payments/methods/`

**Description:** Méthodes de paiement disponibles.

#### `GET /api/payments/summary/`

**Description:** Résumé des paiements de l'utilisateur.

### 6.4. Transactions et Commissions

#### `GET /api/payments/transactions/`

**Description:** Liste des transactions Mobile Money.

#### `GET /api/payments/commissions/`

**Description:** Liste des commissions.

### 6.5. Webhooks Mobile Money

#### `POST /api/payments/webhooks/mtn/`

**Description:** Webhook MTN Money.

#### `POST /api/payments/webhooks/moov/`

**Description:** Webhook Moov Money.

---

## 7. Application `admin_dashboard`

L'application `admin_dashboard` fournit des outils d'administration et de monitoring.

### 7.1. Dashboard Principal

#### `GET /api/admin/dashboard/`

**Description:** Vue d'ensemble du dashboard administrateur.

### 7.2. Statistiques

#### `GET /api/admin/stats/users/`

**Description:** Statistiques des utilisateurs.

#### `GET /api/admin/stats/events/`

**Description:** Statistiques des événements.

#### `GET /api/admin/stats/payments/`

**Description:** Statistiques des paiements.

### 7.3. Santé du Système

#### `GET /api/admin/system/health/`

**Description:** État de santé du système.

### 7.4. Actions et Métriques

#### `GET /api/admin/actions/`

**Description:** Liste des actions administratives.

#### `POST /api/admin/bulk-action/`

**Description:** Exécute une action en masse.

#### `POST /api/admin/quick-action/`

**Description:** Exécute une action rapide.

#### `GET /api/admin/metrics/`

**Description:** Métriques du système.

---

## 8. Application `core`

L'application `core` fournit des fonctionnalités transversales.

### 8.1. Informations de l'Application

#### `GET /api/core/info/`

**Description:** Informations générales sur l'application.

#### `GET /api/core/stats/`

**Description:** Statistiques globales de l'application.

### 8.2. Recherche et Utilitaires

#### `GET /api/core/search/`

**Description:** Recherche globale.

**Paramètres de requête:**
- `q`: Terme de recherche
- `type`: Type de contenu

#### `POST /api/core/upload/`

**Description:** Upload de fichiers.

#### `POST /api/core/report/`

**Description:** Signalement de contenu.

### 8.3. Santé et Maintenance

#### `GET /api/core/health/`

**Description:** Vérification de l'état de santé.

#### `GET /api/core/maintenance/`

**Description:** Mode maintenance.

### 8.4. Feedback et Contact

#### `POST /api/core/feedback/`

**Description:** Soumet un feedback.

#### `GET /api/core/contact/`

**Description:** Liste des messages de contact.

### 8.5. FAQ et Paramètres

#### `GET /api/core/faq/`

**Description:** Liste des questions fréquemment posées.

#### `GET /api/core/settings/`

**Description:** Paramètres de l'application.

---

## Codes de Statut HTTP Communs

- **200 OK:** Requête réussie
- **201 Created:** Ressource créée avec succès
- **204 No Content:** Requête réussie sans contenu de réponse
- **400 Bad Request:** Données de requête invalides
- **401 Unauthorized:** Authentification requise
- **403 Forbidden:** Accès refusé
- **404 Not Found:** Ressource non trouvée
- **500 Internal Server Error:** Erreur serveur

## Authentification

La plupart des endpoints nécessitent une authentification via token. Incluez le token dans l'en-tête de la requête :

```
Authorization: Token <votre_token>
```

## Pagination

Les listes d'objets sont paginées. La réponse inclut :

```json
{
  "count": 100,
  "next": "http://api.example.com/endpoint/?page=2",
  "previous": null,
  "results": [...]
}
```

## Gestion des Erreurs

Les erreurs sont retournées au format JSON :

```json
{
  "error": "Message d'erreur",
  "details": {
    "field": ["Message d'erreur spécifique au champ"]
  }
}
```

