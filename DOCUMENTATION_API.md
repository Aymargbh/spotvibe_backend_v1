# Documentation API SpotVibe

Cette documentation décrit l'API REST de SpotVibe, une plateforme de découverte d'événements locaux.

## 🔗 URL de base

```
https://api.spotvibe.com/api/
```

## 🔐 Authentification

L'API utilise l'authentification par token. Après connexion, incluez le token dans les headers de vos requêtes :

```http
Authorization: Token your_token_here
```

## 📋 Format des réponses

Toutes les réponses sont au format JSON. Les réponses d'erreur suivent ce format :

```json
{
    "error": "Message d'erreur",
    "details": {
        "field": ["Message d'erreur spécifique"]
    }
}
```

Les réponses de succès incluent généralement :

```json
{
    "message": "Opération réussie",
    "data": { ... }
}
```

## 👤 Authentification et Utilisateurs

### Inscription

**POST** `/users/register/`

Crée un nouveau compte utilisateur.

**Paramètres :**
```json
{
    "username": "string (requis)",
    "email": "string (requis)",
    "password": "string (requis, min 8 caractères)",
    "password_confirm": "string (requis)",
    "first_name": "string (requis)",
    "last_name": "string (requis)",
    "telephone": "string (requis)",
    "date_naissance": "date (optionnel)"
}
```

**Réponse :**
```json
{
    "message": "Compte créé avec succès",
    "user": {
        "id": 1,
        "username": "johndoe",
        "email": "john@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "est_verifie": false,
        "followers_count": 0,
        "following_count": 0,
        "events_count": 0
    },
    "token": "abc123..."
}
```

### Connexion

**POST** `/users/login/`

Connecte un utilisateur existant.

**Paramètres :**
```json
{
    "login": "string (email ou username)",
    "password": "string"
}
```

**Réponse :**
```json
{
    "message": "Connexion réussie",
    "user": { ... },
    "token": "abc123..."
}
```

### Déconnexion

**POST** `/users/logout/`

Déconnecte l'utilisateur et supprime le token.

**Headers requis :** `Authorization: Token ...`

### Profil utilisateur

**GET** `/users/profile/`

Récupère le profil de l'utilisateur connecté.

**PUT/PATCH** `/users/profile/`

Modifie le profil de l'utilisateur connecté.

**Paramètres modifiables :**
```json
{
    "first_name": "string",
    "last_name": "string",
    "telephone": "string",
    "date_naissance": "date",
    "photo_profil": "file",
    "bio": "string",
    "notifications_email": "boolean",
    "notifications_push": "boolean"
}
```

### Détails d'un utilisateur

**GET** `/users/{id}/`

Récupère le profil public d'un utilisateur.

### Liste des utilisateurs

**GET** `/users/`

Liste les utilisateurs avec recherche et filtres.

**Paramètres de requête :**
- `search` : Recherche par nom ou username
- `verified` : `true` pour les utilisateurs vérifiés uniquement
- `page` : Numéro de page
- `page_size` : Nombre d'éléments par page (max 100)

### Système de suivi

**POST** `/users/follow/`

Suivre un utilisateur.

```json
{
    "user_id": 123
}
```

**DELETE** `/users/{user_id}/unfollow/`

Ne plus suivre un utilisateur.

**GET** `/users/{user_id}/follow-status/`

Vérifier si on suit un utilisateur.

**GET** `/users/{user_id}/followers/`

Liste des followers d'un utilisateur.

**GET** `/users/{user_id}/following/`

Liste des utilisateurs suivis.

### Vérification d'identité

**POST** `/users/verification/`

Soumettre une demande de vérification.

```json
{
    "document_identite": "file",
    "document_selfie": "file"
}
```

**GET** `/users/verification/status/`

Consulter le statut de vérification.

### Changement de mot de passe

**POST** `/users/change-password/`

```json
{
    "old_password": "string",
    "new_password": "string",
    "new_password_confirm": "string"
}
```

## 📅 Événements

### Liste des événements

**GET** `/events/`

Liste les événements avec filtres et recherche.

**Paramètres de requête :**
- `search` : Recherche textuelle
- `categorie` : ID de catégorie
- `type_acces` : `GRATUIT` ou `PAYANT`
- `createur` : ID du créateur
- `periode` : `today`, `week`, `month`, `past`
- `prix_max` : Prix maximum
- `latitude`, `longitude`, `rayon` : Recherche géographique
- `ordering` : `date_debut`, `date_creation`, `nombre_vues`

**Réponse :**
```json
{
    "count": 150,
    "next": "http://api.spotvibe.com/api/events/?page=2",
    "previous": null,
    "results": [
        {
            "id": 1,
            "titre": "Concert de Jazz",
            "description_courte": "Soirée jazz exceptionnelle",
            "createur": {
                "id": 1,
                "username": "johndoe",
                "first_name": "John",
                "last_name": "Doe"
            },
            "categorie": {
                "id": 1,
                "nom": "Musique",
                "couleur": "#FF5722"
            },
            "date_debut": "2024-03-15T20:00:00Z",
            "date_fin": "2024-03-15T23:00:00Z",
            "lieu": "Salle de concert",
            "type_acces": "PAYANT",
            "prix": 5000,
            "image_couverture": "http://...",
            "statut": "VALIDE",
            "participants_count": 45
        }
    ]
}
```

### Détails d'un événement

**GET** `/events/{id}/`

Récupère les détails complets d'un événement.

**Réponse :**
```json
{
    "id": 1,
    "titre": "Concert de Jazz",
    "description": "Description complète...",
    "description_courte": "Soirée jazz exceptionnelle",
    "createur": { ... },
    "categorie": { ... },
    "date_debut": "2024-03-15T20:00:00Z",
    "date_fin": "2024-03-15T23:00:00Z",
    "lieu": "Salle de concert",
    "adresse": "123 Rue de la Musique, Abidjan",
    "latitude": 5.3364,
    "longitude": -4.0267,
    "lien_google_maps": "https://maps.google.com/...",
    "type_acces": "PAYANT",
    "prix": 5000,
    "capacite_max": 100,
    "image_couverture": "http://...",
    "billetterie_activee": true,
    "commission_billetterie": 10.0,
    "statut": "VALIDE",
    "date_creation": "2024-03-01T10:00:00Z",
    "nombre_vues": 234,
    "nombre_partages": 12,
    "participants_count": 45,
    "is_participating": false,
    "is_liked": false,
    "can_edit": false,
    "revenue": 225000,
    "commission_amount": 22500
}
```

### Créer un événement

**POST** `/events/create/`

Crée un nouvel événement.

**Headers requis :** `Authorization: Token ...`

**Paramètres :**
```json
{
    "titre": "string (requis)",
    "description": "string (requis)",
    "description_courte": "string (requis)",
    "categorie": "integer (ID de catégorie)",
    "date_debut": "datetime (requis)",
    "date_fin": "datetime (requis)",
    "lieu": "string (requis)",
    "adresse": "string (requis)",
    "latitude": "float (optionnel)",
    "longitude": "float (optionnel)",
    "type_acces": "GRATUIT ou PAYANT",
    "prix": "decimal (requis si PAYANT)",
    "capacite_max": "integer (requis)",
    "image_couverture": "file (optionnel)",
    "billetterie_activee": "boolean",
    "commission_billetterie": "decimal"
}
```

### Modifier un événement

**PUT/PATCH** `/events/{id}/update/`

Modifie un événement existant (créateur ou admin uniquement).

### Supprimer un événement

**DELETE** `/events/{id}/delete/`

Supprime un événement (créateur ou admin uniquement).

### Catégories d'événements

**GET** `/events/categories/`

Liste toutes les catégories d'événements actives.

```json
[
    {
        "id": 1,
        "nom": "Musique",
        "description": "Concerts, festivals...",
        "couleur": "#FF5722",
        "icone": "music",
        "events_count": 45
    }
]
```

### Participation aux événements

**POST** `/events/participate/`

Participer à un événement.

```json
{
    "event_id": 123,
    "statut": "CONFIRME" // ou "INTERESSE"
}
```

**DELETE** `/events/{event_id}/cancel-participation/`

Annuler sa participation.

**GET** `/events/{event_id}/participants/`

Liste des participants d'un événement.

### Partage d'événements

**POST** `/events/share/`

Partager un événement.

```json
{
    "event_id": 123,
    "plateforme": "FACEBOOK" // TWITTER, WHATSAPP, TELEGRAM, EMAIL, LIEN
}
```

### Billetterie

**POST** `/events/tickets/purchase/`

Acheter un billet.

```json
{
    "event_id": 123,
    "quantite": 2
}
```

**Réponse :**
```json
{
    "message": "Billet créé avec succès. Procédez au paiement.",
    "ticket": {
        "id": 1,
        "uuid": "abc-123-def",
        "evenement": { ... },
        "prix": 5000,
        "quantite": 2,
        "total_price": 10000,
        "statut": "EN_ATTENTE",
        "date_achat": "2024-03-01T10:00:00Z"
    }
}
```

### Événements de l'utilisateur

**GET** `/events/my-events/`

Événements créés par l'utilisateur connecté.

**GET** `/events/my-participations/`

Participations de l'utilisateur connecté.

**GET** `/events/my-tickets/`

Billets de l'utilisateur connecté.

### Statistiques et tendances

**GET** `/events/stats/`

Statistiques générales des événements.

```json
{
    "total_events": 150,
    "events_today": 5,
    "events_this_week": 23,
    "events_this_month": 67,
    "total_participants": 1234,
    "categories": [ ... ]
}
```

**GET** `/events/trending/`

Événements tendance (plus populaires).

## 💳 Paiements

### Initier un paiement

**POST** `/payments/initiate/`

Initie un paiement Mobile Money.

```json
{
    "type_paiement": "BILLET", // ou "ABONNEMENT"
    "montant": 10000,
    "methode_paiement": "ORANGE_MONEY", // MTN_MONEY, MOOV_MONEY
    "telephone_paiement": "+2250123456789",
    "ticket_id": 123, // si type_paiement = "BILLET"
    "subscription_id": 456 // si type_paiement = "ABONNEMENT"
}
```

### Statut d'un paiement

**GET** `/payments/{uuid}/status/`

Consulte le statut d'un paiement.

### Historique des paiements

**GET** `/payments/history/`

Historique des paiements de l'utilisateur.

### Demander un remboursement

**POST** `/payments/refund/`

```json
{
    "payment_id": 123,
    "raison": "ANNULATION_EVENEMENT",
    "description": "L'événement a été annulé"
}
```

## 📊 Abonnements

### Plans d'abonnement

**GET** `/subscriptions/plans/`

Liste des plans d'abonnement disponibles.

```json
[
    {
        "id": 1,
        "nom": "Standard",
        "type_plan": "STANDARD",
        "prix": 2000,
        "duree": 30,
        "description": "Plan de base",
        "max_evenements_par_mois": 3,
        "commission_reduite": false,
        "support_prioritaire": false,
        "analytics_avances": false
    }
]
```

### S'abonner

**POST** `/subscriptions/subscribe/`

```json
{
    "plan_id": 1
}
```

### Mon abonnement

**GET** `/subscriptions/my-subscription/`

Détails de l'abonnement actuel.

### Annuler un abonnement

**POST** `/subscriptions/cancel/`

Annule l'abonnement actuel.

## 🔔 Notifications

### Mes notifications

**GET** `/notifications/`

Liste des notifications de l'utilisateur.

**Paramètres de requête :**
- `type_notification` : Type de notification
- `statut` : `NOUVEAU`, `VU`, `LU`
- `priorite` : `BASSE`, `NORMALE`, `HAUTE`, `CRITIQUE`

### Marquer comme lu

**POST** `/notifications/{id}/mark-read/`

Marque une notification comme lue.

### Préférences de notification

**GET** `/notifications/preferences/`

Récupère les préférences de notification.

**PUT** `/notifications/preferences/`

Modifie les préférences de notification.

```json
{
    "preferences": [
        {
            "type_notification": "NOUVEL_EVENEMENT",
            "canal": "EMAIL",
            "actif": true,
            "frequence": "IMMEDIATE"
        }
    ]
}
```

### Tokens push

**POST** `/notifications/push-tokens/`

Enregistre un token push pour les notifications.

```json
{
    "token": "firebase_token_here",
    "plateforme": "ANDROID", // ou "IOS"
    "nom_appareil": "Samsung Galaxy S21"
}
```

## 📱 Codes d'erreur

| Code | Description |
|------|-------------|
| 400 | Requête invalide |
| 401 | Non authentifié |
| 403 | Accès refusé |
| 404 | Ressource introuvable |
| 429 | Trop de requêtes |
| 500 | Erreur serveur |

## 🔄 Pagination

Les listes sont paginées automatiquement :

```json
{
    "count": 150,
    "next": "http://api.spotvibe.com/api/events/?page=3",
    "previous": "http://api.spotvibe.com/api/events/?page=1",
    "results": [ ... ]
}
```

**Paramètres :**
- `page` : Numéro de page (défaut: 1)
- `page_size` : Éléments par page (défaut: 20, max: 100)

## 🌍 Géolocalisation

Pour la recherche géographique, utilisez :

```
GET /events/?latitude=5.3364&longitude=-4.0267&rayon=10
```

- `latitude` : Latitude en degrés décimaux
- `longitude` : Longitude en degrés décimaux  
- `rayon` : Rayon de recherche en kilomètres (défaut: 10)

## 📄 Upload de fichiers

Pour les uploads (images, documents), utilisez `multipart/form-data` :

```http
POST /users/verification/
Content-Type: multipart/form-data

document_identite: [file]
document_selfie: [file]
```

## 🔒 Limites de taux

- **Authentifié** : 1000 requêtes/heure
- **Non authentifié** : 100 requêtes/heure
- **Upload** : 10 fichiers/minute

## 📞 Support

Pour toute question sur l'API :

- **Email** : api-support@spotvibe.com
- **Documentation** : [docs.spotvibe.com](https://docs.spotvibe.com)
- **Status** : [status.spotvibe.com](https://status.spotvibe.com)

---

**Version de l'API :** 1.0  
**Dernière mise à jour :** Mars 2024

