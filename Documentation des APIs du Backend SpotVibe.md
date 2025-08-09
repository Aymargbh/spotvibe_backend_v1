# Documentation des APIs du Backend SpotVibe

Ce document fournit une documentation complète des APIs exposées par le backend de SpotVibe. Il est conçu pour aider les développeurs frontend, en particulier ceux utilisant Flutter, à interagir avec le backend sans avoir à plonger dans le code source. Chaque section décrit une application, ses endpoints, les méthodes HTTP supportées, les corps de requête et de réponse attendus, ainsi que les codes de statut HTTP pertinents.

## 1. Application `authentication`

L'application `authentication` gère tout ce qui concerne l'authentification des utilisateurs, y compris l'authentification sociale, la gestion des mots de passe, l'authentification à deux facteurs et le suivi des tentatives de connexion.

### 1.1. Authentification Sociale

#### `POST /api/auth/google/`

**Description:** Authentifie un utilisateur via Google OAuth2. Si l'utilisateur n'existe pas, un nouveau compte est créé et lié au compte Google.

**Corps de la requête (JSON):**
```json
{
  "access_token": "<token_d_acces_google>"
}
```

**Réponses (JSON):**
- **200 OK:** Authentification réussie. Retourne les informations de l'utilisateur et les tokens JWT.
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
- **400 Bad Request:** Token invalide ou autre erreur de validation.
  ```json
  {
    "error": "Message d'erreur"
  }
  ```

#### `POST /api/auth/facebook/`

**Description:** Authentifie un utilisateur via Facebook OAuth2. Similaire à l'authentification Google.

**Corps de la requête (JSON):**
```json
{
  "access_token": "<token_d_acces_facebook>"
}
```

**Réponses (JSON):**
- **200 OK:** Authentification réussie. Retourne les informations de l'utilisateur et les tokens JWT.
  ```json
  {
    "access": "<jwt_access_token>",
    "refresh": "<jwt_refresh_token>",
    "user": {
      "id": 1,
      "username": "utilisateur_facebook",
      "email": "utilisateur@facebook.com",
      "first_name": "Nom",
      "last_name": "Prénom",
      "photo_profil": "/media/profiles/photo.jpg",
      "est_verifie": false
    }
  }
  ```
- **400 Bad Request:** Token invalide ou autre erreur de validation.
  ```json
  {
    "error": "Message d'erreur"
  }
  ```

### 1.2. Gestion des Comptes Sociaux

#### `GET /api/auth/social-accounts/`

**Description:** Récupère la liste des comptes sociaux liés à l'utilisateur authentifié.

**Réponses (JSON):**
- **200 OK:** Liste des comptes sociaux.
  ```json
  [
    {
      "id": 1,
      "provider": "GOOGLE",
      "social_id": "1234567890",
      "email": "utilisateur@gmail.com",
      "nom_complet": "Nom Prénom",
      "photo_url": "https://photo.google.com/profile.jpg"
    }
  ]
  ```

#### `POST /api/auth/social-accounts/<str:provider>/disconnect/`

**Description:** Déconnecte un compte social spécifique de l'utilisateur authentifié.

**Paramètres de l'URL:**
- `provider`: Le fournisseur du compte social à déconnecter (ex: `google`, `facebook`).

**Réponses (JSON):**
- **200 OK:** Compte social déconnecté avec succès.
  ```json
  {
    "message": "Compte social déconnecté avec succès."
  }
  ```
- **400 Bad Request:** Erreur lors de la déconnexion (ex: compte non trouvé).
  ```json
  {
    "error": "Message d'erreur"
  }
  ```

### 1.3. Authentification à Deux Facteurs (2FA)

#### `POST /api/auth/2fa/setup/`

**Description:** Initialise la configuration de l'authentification à deux facteurs pour l'utilisateur. Retourne un code QR ou des instructions selon la méthode choisie.

**Corps de la requête (JSON):**
```json
{
  "method": "SMS" // ou "EMAIL", "TOTP"
}
```

**Réponses (JSON):**
- **200 OK:** Configuration 2FA initiée. Retourne les détails pour la vérification.
  ```json
  {
    "message": "Configuration 2FA initiée. Veuillez vérifier votre téléphone/email ou scanner le QR code.",
    "qr_code_url": "<url_qr_code>", // Pour TOTP
    "secret_key": "<cle_secrete>" // Pour TOTP
  }
  ```
- **400 Bad Request:** Méthode invalide ou 2FA déjà activée.

#### `POST /api/auth/2fa/verify/`

**Description:** Vérifie le code 2FA fourni par l'utilisateur pour activer ou se connecter avec 2FA.

**Corps de la requête (JSON):**
```json
{
  "code": "123456" // Code reçu par SMS/Email ou généré par l'application TOTP
}
```

**Réponses (JSON):**
- **200 OK:** Vérification 2FA réussie. Si c'était une configuration, 2FA est activée.
  ```json
  {
    "message": "Vérification 2FA réussie."
  }
  ```
- **400 Bad Request:** Code invalide ou expiré.

### 1.4. Réinitialisation de Mot de Passe

#### `POST /api/auth/password-reset/`

**Description:** Demande une réinitialisation de mot de passe. Un email avec un lien de réinitialisation est envoyé à l'utilisateur.

**Corps de la requête (JSON):**
```json
{
  "email": "utilisateur@example.com"
}
```

**Réponses (JSON):**
- **200 OK:** Demande de réinitialisation envoyée (même si l'email n'existe pas pour des raisons de sécurité).
  ```json
  {
    "message": "Si l'email est enregistré, un lien de réinitialisation a été envoyé."
  }
  ```

#### `POST /api/auth/password-reset/confirm/`

**Description:** Confirme la réinitialisation du mot de passe avec le token reçu par email et le nouveau mot de passe.

**Corps de la requête (JSON):**
```json
{
  "token": "<token_de_reinitialisation>",
  "new_password": "nouveau_mot_de_passe",
  "confirm_password": "nouveau_mot_de_passe"
}
```

**Réponses (JSON):**
- **200 OK:** Mot de passe réinitialisé avec succès.
  ```json
  {
    "message": "Votre mot de passe a été réinitialisé avec succès."
  }
  ```
- **400 Bad Request:** Token invalide, expiré, ou mots de passe ne correspondent pas.

### 1.5. Historique et Statut d'Authentification

#### `GET /api/auth/login-attempts/`

**Description:** Récupère l'historique des tentatives de connexion de l'utilisateur authentifié.

**Réponses (JSON):**
- **200 OK:** Liste des tentatives de connexion.
  ```json
  [
    {
      "id": 1,
      "email_tente": "utilisateur@example.com",
      "statut": "REUSSI",
      "date_tentative": "2024-07-30T10:00:00Z",
      "adresse_ip": "192.168.1.1"
    }
  ]
  ```

#### `GET /api/auth/status/`

**Description:** Vérifie le statut d'authentification de l'utilisateur (connecté, 2FA activé, etc.).

**Réponses (JSON):**
- **200 OK:** Statut d'authentification.
  ```json
  {
    "is_authenticated": true,
    "username": "utilisateur",
    "email": "utilisateur@example.com",
    "2fa_enabled": true,
    "last_login": "2024-07-30T10:00:00Z"
  }
  ```

## 2. Application `users`

L'application `users` gère la création, la gestion et l'interaction avec les profils utilisateurs, y compris l'inscription, la connexion, la vérification d'identité et le système de suivi.

### 2.1. Authentification et Gestion de Compte

#### `POST /api/users/register/`

**Description:** Enregistre un nouvel utilisateur.

**Corps de la requête (JSON):**
```json
{
  "username": "nouvel_utilisateur",
  "email": "nouvel_utilisateur@example.com",
  "password": "mot_de_passe_securise",
  "telephone": "+22997000000",
  "first_name": "Nom",
  "last_name": "Prénom"
}
```

**Réponses (JSON):**
- **201 Created:** Utilisateur enregistré avec succès. Un email de vérification peut être envoyé.
  ```json
  {
    "message": "Utilisateur enregistré avec succès. Veuillez vérifier votre email.",
    "user": {
      "id": 2,
      "username": "nouvel_utilisateur",
      "email": "nouvel_utilisateur@example.com"
    }
  }
  ```
- **400 Bad Request:** Données invalides (ex: email déjà utilisé, mot de passe trop faible).

#### `POST /api/users/login/`

**Description:** Connecte un utilisateur et retourne les tokens JWT.

**Corps de la requête (JSON):**
```json
{
  "email": "utilisateur@example.com",
  "password": "mot_de_passe"
}
```

**Réponses (JSON):**
- **200 OK:** Connexion réussie. Retourne les tokens d'accès et de rafraîchissement.
  ```json
  {
    "access": "<jwt_access_token>",
    "refresh": "<jwt_refresh_token>"
  }
  ```
- **401 Unauthorized:** Identifiants invalides.

#### `POST /api/users/logout/`

**Description:** Déconnecte l'utilisateur en invalidant le token de rafraîchissement.

**Corps de la requête (JSON):**
```json
{
  "refresh": "<jwt_refresh_token>"
}
```

**Réponses (JSON):**
- **200 OK:** Déconnexion réussie.
  ```json
  {
    "message": "Déconnexion réussie."
  }
  ```
- **400 Bad Request:** Token invalide.

### 2.2. Profil Utilisateur

#### `GET /api/users/profile/`

**Description:** Récupère les détails du profil de l'utilisateur authentifié.

**Réponses (JSON):**
- **200 OK:** Détails du profil.
  ```json
  {
    "id": 1,
    "username": "utilisateur",
    "email": "utilisateur@example.com",
    "first_name": "Nom",
    "last_name": "Prénom",
    "telephone": "+22997000000",
    "date_naissance": "1990-01-01",
    "photo_profil": "/media/profiles/photo.jpg",
    "bio": "Ma biographie.",
    "est_verifie": true,
    "notifications_email": true,
    "notifications_push": true
  }
  ```

#### `PUT /api/users/profile/`

**Description:** Met à jour les détails du profil de l'utilisateur authentifié.

**Corps de la requête (JSON):**
```json
{
  "first_name": "Nouveau Nom",
  "bio": "Nouvelle biographie."
  // ... autres champs modifiables
}
```

**Réponses (JSON):**
- **200 OK:** Profil mis à jour avec succès.
  ```json
  {
    "message": "Profil mis à jour avec succès.",
    "user": { /* ... détails du profil mis à jour ... */ }
  }
  ```
- **400 Bad Request:** Données invalides.

#### `POST /api/users/change-password/`

**Description:** Permet à l'utilisateur authentifié de changer son mot de passe.

**Corps de la requête (JSON):**
```json
{
  "old_password": "ancien_mot_de_passe",
  "new_password": "nouveau_mot_de_passe",
  "confirm_password": "nouveau_mot_de_passe"
}
```

**Réponses (JSON):**
- **200 OK:** Mot de passe changé avec succès.
  ```json
  {
    "message": "Mot de passe changé avec succès."
  }
  ```
- **400 Bad Request:** Ancien mot de passe incorrect ou nouveaux mots de passe ne correspondent pas.

#### `GET /api/users/stats/`

**Description:** Récupère les statistiques de l'utilisateur authentifié (nombre d'événements créés, followers, etc.).

**Réponses (JSON):**
- **200 OK:** Statistiques utilisateur.
  ```json
  {
    "events_created_count": 5,
    "followers_count": 120,
    "following_count": 50,
    "total_tickets_purchased": 15
  }
  ```

### 2.3. Vérification d'Identité

#### `POST /api/users/verification/`

**Description:** Soumet des documents pour la vérification d'identité de l'utilisateur.

**Corps de la requête (Multipart Form Data):**
- `document_identite`: Fichier du document d'identité.
- `document_selfie`: Fichier du selfie avec le document (optionnel).

**Réponses (JSON):**
- **201 Created:** Documents soumis avec succès. La vérification est en attente.
  ```json
  {
    "message": "Documents soumis pour vérification. Statut: EN_ATTENTE."
  }
  ```
- **400 Bad Request:** Fichiers manquants ou invalides.

#### `GET /api/users/verification/status/`

**Description:** Récupère le statut de la vérification d'identité de l'utilisateur.

**Réponses (JSON):**
- **200 OK:** Statut de vérification.
  ```json
  {
    "statut": "EN_ATTENTE", // ou "APPROUVE", "REJETE", "EXPIRE"
    "date_soumission": "2024-07-30T10:00:00Z",
    "commentaire_admin": ""
  }
  ```

### 2.4. Système de Suivi

#### `POST /api/users/follow/`

**Description:** Permet à l'utilisateur authentifié de suivre un autre utilisateur.

**Corps de la requête (JSON):**
```json
{
  "user_id": 2 // ID de l'utilisateur à suivre
}
```

**Réponses (JSON):**
- **200 OK:** Suivi réussi.
  ```json
  {
    "message": "Utilisateur suivi avec succès."
  }
  ```
- **400 Bad Request:** Impossible de suivre l'utilisateur (ex: déjà suivi, auto-suivi).

#### `POST /api/users/<int:user_id>/unfollow/`

**Description:** Permet à l'utilisateur authentifié de ne plus suivre un autre utilisateur.

**Paramètres de l'URL:**
- `user_id`: L'ID de l'utilisateur à ne plus suivre.

**Réponses (JSON):**
- **200 OK:** Désabonnement réussi.
  ```json
  {
    "message": "Utilisateur désabonné avec succès."
  }
  ```
- **400 Bad Request:** Erreur lors du désabonnement.

#### `GET /api/users/<int:user_id>/follow-status/`

**Description:** Vérifie si l'utilisateur authentifié suit un utilisateur spécifique.

**Paramètres de l'URL:**
- `user_id`: L'ID de l'utilisateur à vérifier.

**Réponses (JSON):**
- **200 OK:** Statut de suivi.
  ```json
  {
    "is_following": true
  }
  ```

#### `GET /api/users/<int:user_id>/followers/`

**Description:** Récupère la liste des followers d'un utilisateur spécifique.

**Paramètres de l'URL:**
- `user_id`: L'ID de l'utilisateur.

**Réponses (JSON):**
- **200 OK:** Liste des followers.
  ```json
  [
    {
      "id": 3,
      "username": "follower_user",
      "photo_profil": "/media/profiles/follower.jpg"
    }
  ]
  ```

#### `GET /api/users/<int:user_id>/following/`

**Description:** Récupère la liste des utilisateurs suivis par un utilisateur spécifique.

**Paramètres de l'URL:**
- `user_id`: L'ID de l'utilisateur.

**Réponses (JSON):**
- **200 OK:** Liste des utilisateurs suivis.
  ```json
  [
    {
      "id": 4,
      "username": "followed_user",
      "photo_profil": "/media/profiles/followed.jpg"
    }
  ]
  ```

### 2.5. Liste et Détails des Utilisateurs

#### `GET /api/users/`

**Description:** Récupère la liste de tous les utilisateurs enregistrés.

**Réponses (JSON):**
- **200 OK:** Liste paginée des utilisateurs.
  ```json
  {
    "count": 100,
    "next": "<url_page_suivante>",
    "previous": null,
    "results": [
      {
        "id": 1,
        "username": "utilisateur1",
        "email": "user1@example.com",
        "photo_profil": "/media/profiles/user1.jpg"
      }
    ]
  }
  ```

#### `GET /api/users/<int:pk>/`

**Description:** Récupère les détails d'un utilisateur spécifique par son ID.

**Paramètres de l'URL:**
- `pk`: L'ID de l'utilisateur.

**Réponses (JSON):**
- **200 OK:** Détails de l'utilisateur.
  ```json
  {
    "id": 1,
    "username": "utilisateur1",
    "email": "user1@example.com",
    "first_name": "Nom1",
    "last_name": "Prénom1",
    "photo_profil": "/media/profiles/user1.jpg",
    "bio": "Biographie de l'utilisateur1."
  }
  ```
- **404 Not Found:** Utilisateur non trouvé.

## 3. Application `core`

L'application `core` fournit des fonctionnalités transversales et des utilitaires pour l'ensemble de l'application SpotVibe, y compris les informations sur l'application, la recherche globale, le téléchargement de fichiers, les rapports de contenu, la vérification de l'état de santé du système, et la gestion des FAQ.

### 3.1. Informations de l'Application

#### `GET /api/core/info/`

**Description:** Récupère les informations générales sur l'application (version, nom, etc.).

**Réponses (JSON):**
- **200 OK:** Informations sur l'application.
  ```json
  {
    "app_name": "SpotVibe",
    "version": "1.0.0",
    "description": "Plateforme de gestion d'événements et de billetterie.",
    "contact_email": "contact@spotvibe.com"
  }
  ```

#### `GET /api/core/stats/`

**Description:** Récupère les statistiques globales de l'application (nombre d'utilisateurs, d'événements, etc.).

**Réponses (JSON):**
- **200 OK:** Statistiques globales.
  ```json
  {
    "total_users": 1500,
    "total_events": 500,
    "active_subscriptions": 250,
    "total_revenue": 15000000 // FCFA
  }
  ```

### 3.2. Recherche et Utilitaires

#### `GET /api/core/search/`

**Description:** Effectue une recherche globale sur différents types de contenu (utilisateurs, événements, etc.).

**Paramètres de requête:**
- `q`: Le terme de recherche.
- `type`: Le type de contenu à rechercher (optionnel, ex: `users`, `events`).

**Réponses (JSON):**
- **200 OK:** Résultats de la recherche.
  ```json
  {
    "users": [
      { /* ... détails utilisateur ... */ }
    ],
    "events": [
      { /* ... détails événement ... */ }
    ]
  }
  ```

#### `POST /api/core/upload/`

**Description:** Permet le téléchargement de fichiers (images, documents) vers le serveur.

**Corps de la requête (Multipart Form Data):**
- `file`: Le fichier à télécharger.
- `type`: Le type de fichier (ex: `image`, `document`).

**Réponses (JSON):**
- **200 OK:** Fichier téléchargé avec succès.
  ```json
  {
    "message": "Fichier téléchargé avec succès.",
    "file_url": "/media/uploads/image.jpg"
  }
  ```
- **400 Bad Request:** Fichier invalide ou trop volumineux.

#### `POST /api/core/report/`

**Description:** Permet aux utilisateurs de signaler du contenu inapproprié.

**Corps de la requête (JSON):**
```json
{
  "content_type": "event", // ou "user", "comment"
  "object_id": 123, // ID de l'objet signalé
  "reason": "Contenu offensant",
  "description": "Description détaillée du problème."
}
```

**Réponses (JSON):**
- **201 Created:** Rapport soumis avec succès.
  ```json
  {
    "message": "Contenu signalé avec succès."
  }
  ```
- **400 Bad Request:** Données invalides.

### 3.3. Santé et Maintenance

#### `GET /api/core/health/`

**Description:** Vérifie l'état de santé du backend (connexion à la base de données, services externes, etc.).

**Réponses (JSON):**
- **200 OK:** Le système est opérationnel.
  ```json
  {
    "status": "OK",
    "database": "connected",
    "redis": "connected"
  }
  ```
- **500 Internal Server Error:** Problème de santé.

#### `GET /api/core/maintenance/`

**Description:** Récupère le statut de maintenance actuel du système.

**Réponses (JSON):**
- **200 OK:** Statut de maintenance.
  ```json
  {
    "in_maintenance": true,
    "message": "Maintenance prévue le 2024-08-01 de 02:00 à 04:00 UTC."
  }
  ```

### 3.4. Feedback et Contact

#### `POST /api/core/feedback/`

**Description:** Permet aux utilisateurs de soumettre des commentaires ou des suggestions.

**Corps de la requête (JSON):**
```json
{
  "subject": "Suggestion de fonctionnalité",
  "message": "J'aimerais voir une option pour...",
  "email": "mon_email@example.com" // Optionnel si authentifié
}
```

**Réponses (JSON):**
- **201 Created:** Feedback soumis avec succès.
  ```json
  {
    "message": "Votre feedback a été soumis avec succès."
  }
  ```

#### `GET /api/core/contact/`

**Description:** Récupère la liste des messages de contact (pour les administrateurs).

**Réponses (JSON):**
- **200 OK:** Liste des messages de contact.
  ```json
  [
    {
      "id": 1,
      "nom": "Utilisateur Test",
      "email": "test@example.com",
      "sujet": "Problème de connexion",
      "statut": "NOUVEAU"
    }
  ]
  ```

### 3.5. FAQ et Paramètres

#### `GET /api/core/faq/`

**Description:** Récupère la liste des questions fréquemment posées.

**Réponses (JSON):**
- **200 OK:** Liste des FAQ.
  ```json
  [
    {
      "id": 1,
      "question": "Comment réinitialiser mon mot de passe?",
      "reponse": "Vous pouvez réinitialiser votre mot de passe en cliquant sur 'Mot de passe oublié' sur la page de connexion.",
      "categorie": "COMPTE"
    }
  ]
  ```

#### `GET /api/core/settings/`

**Description:** Récupère les paramètres de configuration de l'application.

**Réponses (JSON):**
- **200 OK:** Paramètres de l'application.
  ```json
  [
    {
      "cle": "MAX_IMAGE_SIZE",
      "valeur": "5",
      "type_valeur": "INTEGER",
      "description": "Taille maximale des images uploadées en MB."
    }
  ]
  ```

## 4. Application `events`

L'application `events` gère la création, la gestion, la participation et la billetterie des événements. Elle permet aux utilisateurs de découvrir, s'inscrire et acheter des billets pour divers événements.

### 4.1. Catégories d'Événements

#### `GET /api/events/categories/`

**Description:** Récupère la liste de toutes les catégories d'événements disponibles.

**Réponses (JSON):**
- **200 OK:** Liste des catégories d'événements.
  ```json
  [
    {
      "id": 1,
      "nom": "Concert",
      "description": "Événements musicaux en direct.",
      "icone": "fas fa-music",
      "couleur": "#FF0000"
    }
  ]
  ```

### 4.2. CRUD Événements

#### `GET /api/events/`

**Description:** Récupère la liste de tous les événements. Supporte la pagination, le filtrage et la recherche.

**Paramètres de requête:**
- `page`: Numéro de la page.
- `search`: Terme de recherche pour le titre ou la description.
- `category`: ID de la catégorie d'événement.
- `status`: Statut de l'événement (ex: `VALIDE`, `TERMINE`).

**Réponses (JSON):**
- **200 OK:** Liste paginée des événements.
  ```json
  {
    "count": 50,
    "next": "<url_page_suivante>",
    "previous": null,
    "results": [
      {
        "id": 1,
        "titre": "Festival de Jazz",
        "description_courte": "Un festival annuel de jazz.",
        "date_debut": "2024-08-15T18:00:00Z",
        "lieu": "Parc Central",
        "image_couverture": "/media/events/covers/jazz_festival.jpg",
        "statut": "VALIDE"
      }
    ]
  }
  ```

#### `POST /api/events/create/`

**Description:** Crée un nouvel événement.

**Corps de la requête (Multipart Form Data):**
- `titre`: Titre de l'événement.
- `description`: Description détaillée.
- `date_debut`: Date et heure de début (format ISO 8601).
- `date_fin`: Date et heure de fin (format ISO 8601).
- `lieu`: Nom du lieu.
- `adresse`: Adresse complète.
- `categorie`: ID de la catégorie.
- `type_acces`: Type d'accès (`GRATUIT`, `PAYANT`, `INVITATION`).
- `prix`: Prix (si `PAYANT`).
- `image_couverture`: Fichier image.

**Réponses (JSON):**
- **201 Created:** Événement créé avec succès.
  ```json
  {
    "message": "Événement créé avec succès.",
    "event": { /* ... détails de l'événement créé ... */ }
  }
  ```
- **400 Bad Request:** Données invalides.

#### `GET /api/events/<int:pk>/`

**Description:** Récupère les détails d'un événement spécifique.

**Paramètres de l'URL:**
- `pk`: L'ID de l'événement.

**Réponses (JSON):**
- **200 OK:** Détails de l'événement.
  ```json
  {
    "id": 1,
    "titre": "Festival de Jazz",
    "description": "Un festival annuel de jazz avec des artistes internationaux.",
    "date_debut": "2024-08-15T18:00:00Z",
    "date_fin": "2024-08-17T23:00:00Z",
    "lieu": "Parc Central",
    "adresse": "123 Rue de la Musique, Ville",
    "latitude": 48.8566,
    "longitude": 2.3522,
    "createur": { "id": 1, "username": "organisateur" },
    "categorie": { "id": 1, "nom": "Concert" },
    "type_acces": "PAYANT",
    "prix": "5000.00",
    "image_couverture": "/media/events/covers/jazz_festival.jpg",
    "statut": "VALIDE",
    "nombre_vues": 1200,
    "nombre_partages": 50
  }
  ```
- **404 Not Found:** Événement non trouvé.

#### `PUT /api/events/<int:pk>/update/`

**Description:** Met à jour un événement existant.

**Paramètres de l'URL:**
- `pk`: L'ID de l'événement à mettre à jour.

**Corps de la requête (Multipart Form Data ou JSON):**
- Champs à modifier (ex: `titre`, `description`, `date_debut`).

**Réponses (JSON):**
- **200 OK:** Événement mis à jour avec succès.
  ```json
  {
    "message": "Événement mis à jour avec succès.",
    "event": { /* ... détails de l'événement mis à jour ... */ }
  }
  ```
- **400 Bad Request:** Données invalides.
- **403 Forbidden:** L'utilisateur n'est pas autorisé à modifier cet événement.

#### `DELETE /api/events/<int:pk>/delete/`

**Description:** Supprime un événement.

**Paramètres de l'URL:**
- `pk`: L'ID de l'événement à supprimer.

**Réponses (JSON):**
- **204 No Content:** Événement supprimé avec succès.
- **403 Forbidden:** L'utilisateur n'est pas autorisé à supprimer cet événement.
- **404 Not Found:** Événement non trouvé.

### 4.3. Participations aux Événements

#### `POST /api/events/participate/`

**Description:** Permet à un utilisateur de s'inscrire ou d'exprimer son intérêt pour un événement.

**Corps de la requête (JSON):**
```json
{
  "event_id": 1, // ID de l'événement
  "status": "PARTICIPE" // ou "INTERESSE"
}
```

**Réponses (JSON):**
- **201 Created:** Participation enregistrée.
  ```json
  {
    "message": "Participation enregistrée avec succès."
  }
  ```
- **400 Bad Request:** Déjà inscrit ou événement invalide.

#### `POST /api/events/<int:event_id>/cancel-participation/`

**Description:** Annule la participation d'un utilisateur à un événement.

**Paramètres de l'URL:**
- `event_id`: L'ID de l'événement.

**Réponses (JSON):**
- **200 OK:** Participation annulée.
  ```json
  {
    "message": "Participation annulée avec succès."
  }
  ```
- **400 Bad Request:** Non participant ou erreur.

#### `GET /api/events/<int:event_id>/participants/`

**Description:** Récupère la liste des participants à un événement.

**Paramètres de l'URL:**
- `event_id`: L'ID de l'événement.

**Réponses (JSON):**
- **200 OK:** Liste des participants.
  ```json
  [
    {
      "id": 1,
      "username": "participant1",
      "photo_profil": "/media/profiles/participant1.jpg",
      "statut_participation": "PARTICIPE"
    }
  ]
  ```

### 4.4. Partages d'Événements

#### `POST /api/events/share/`

**Description:** Enregistre un partage d'événement sur une plateforme sociale.

**Corps de la requête (JSON):**
```json
{
  "event_id": 1,
  "platform": "FACEBOOK", // ou "TWITTER", "WHATSAPP", etc.
  "shared_link": "https://example.com/event/1"
}
```

**Réponses (JSON):**
- **201 Created:** Partage enregistré.
  ```json
  {
    "message": "Partage enregistré avec succès."
  }
  ```

### 4.5. Billetterie

#### `POST /api/events/tickets/purchase/`

**Description:** Initie l'achat d'un billet pour un événement.

**Corps de la requête (JSON):**
```json
{
  "event_id": 1,
  "quantity": 1,
  "payment_method": "MOMO_MTN",
  "phone_number": "+22997000000"
}
```

**Réponses (JSON):**
- **201 Created:** Achat initié. Le statut du paiement sera `EN_ATTENTE`.
  ```json
  {
    "message": "Achat de billet initié. Veuillez confirmer le paiement sur votre téléphone.",
    "payment_uuid": "<uuid_du_paiement>"
  }
  ```
- **400 Bad Request:** Événement non payant, quantité invalide, etc.

### 4.6. Événements Utilisateur

#### `GET /api/events/my-events/`

**Description:** Récupère la liste des événements créés par l'utilisateur authentifié.

**Réponses (JSON):**
- **200 OK:** Liste des événements créés.
  ```json
  [
    { /* ... détails événement ... */ }
  ]
  ```

#### `GET /api/events/my-participations/`

**Description:** Récupère la liste des événements auxquels l'utilisateur authentifié participe ou est intéressé.

**Réponses (JSON):**
- **200 OK:** Liste des participations.
  ```json
  [
    { /* ... détails participation ... */ }
  ]
  ```

#### `GET /api/events/my-tickets/`

**Description:** Récupère la liste des billets achetés par l'utilisateur authentifié.

**Réponses (JSON):**
- **200 OK:** Liste des billets.
  ```json
  [
    {
      "id": 1,
      "uuid": "<uuid_billet>",
      "evenement_titre": "Concert de Rock",
      "prix": "10000.00",
      "statut": "PAYE",
      "code_qr_url": "/media/tickets/qr_code.png"
    }
  ]
  ```

### 4.7. Statistiques et Tendances

#### `GET /api/events/stats/`

**Description:** Récupère les statistiques générales sur les événements (nombre total, événements actifs, etc.).

**Réponses (JSON):**
- **200 OK:** Statistiques événements.
  ```json
  {
    "total_events": 500,
    "active_events": 300,
    "upcoming_events": 150,
    "total_participants": 10000
  }
  ```

#### `GET /api/events/trending/`

**Description:** Récupère la liste des événements tendance (les plus populaires, les plus consultés).

**Réponses (JSON):**
- **200 OK:** Liste des événements tendance.
  ```json
  [
    { /* ... détails événement ... */ }
  ]
  ```

## 5. Application `subscriptions`

L'application `subscriptions` gère les plans d'abonnement, les abonnements des utilisateurs, et les fonctionnalités associées. Elle permet aux utilisateurs de souscrire, renouveler, annuler ou mettre à niveau leurs abonnements.

### 5.1. Plans d'Abonnement

#### `GET /api/subscriptions/plans/`

**Description:** Récupère la liste de tous les plans d'abonnement disponibles.

**Réponses (JSON):**
- **200 OK:** Liste des plans d'abonnement.
  ```json
  [
    {
      "id": 1,
      "nom": "Standard",
      "type_plan": "STANDARD",
      "prix": "10000.00",
      "duree": "MENSUEL",
      "description": "Accès de base aux fonctionnalités.",
      "max_evenements_par_mois": 1,
      "commission_reduite": "10.00",
      "support_prioritaire": false
    }
  ]
  ```

#### `GET /api/subscriptions/plans/<int:pk>/`

**Description:** Récupère les détails d'un plan d'abonnement spécifique.

**Paramètres de l'URL:**
- `pk`: L'ID du plan d'abonnement.

**Réponses (JSON):**
- **200 OK:** Détails du plan d'abonnement.
  ```json
  {
    "id": 1,
    "nom": "Standard",
    "type_plan": "STANDARD",
    "prix": "10000.00",
    "duree": "MENSUEL",
    "description": "Accès de base aux fonctionnalités.",
    "max_evenements_par_mois": 1,
    "commission_reduite": "10.00",
    "support_prioritaire": false,
    "features": [
      {
        "nom": "Création d'événements",
        "inclus": true,
        "limite": "1 par mois"
      }
    ]
  }
  ```
- **404 Not Found:** Plan non trouvé.

#### `GET /api/subscriptions/compare/`

**Description:** Compare les fonctionnalités et les prix des différents plans d'abonnement.

**Réponses (JSON):**
- **200 OK:** Comparaison des plans.
  ```json
  {
    "plans": [
      { /* ... détails plan Standard ... */ },
      { /* ... détails plan Premium ... */ },
      { /* ... détails plan Gold ... */ }
    ],
    "common_features": [
      "Accès à la plateforme",
      "Support standard"
    ]
  }
  ```

### 5.2. Abonnements Utilisateur

#### `GET /api/subscriptions/`

**Description:** Récupère la liste des abonnements de l'utilisateur authentifié.

**Réponses (JSON):**
- **200 OK:** Liste des abonnements.
  ```json
  [
    {
      "id": 1,
      "plan_nom": "Standard",
      "date_debut": "2024-07-01T00:00:00Z",
      "date_fin": "2024-07-31T23:59:59Z",
      "statut": "ACTIF",
      "prix_paye": "10000.00"
    }
  ]
  ```

#### `GET /api/subscriptions/<int:pk>/`

**Description:** Récupère les détails d'un abonnement spécifique de l'utilisateur.

**Paramètres de l'URL:**
- `pk`: L'ID de l'abonnement.

**Réponses (JSON):**
- **200 OK:** Détails de l'abonnement.
  ```json
  {
    "id": 1,
    "plan": { "id": 1, "nom": "Standard" },
    "date_debut": "2024-07-01T00:00:00Z",
    "date_fin": "2024-07-31T23:59:59Z",
    "statut": "ACTIF",
    "prix_paye": "10000.00",
    "renouvellement_automatique": true,
    "evenements_crees_ce_mois": 0
  }
  ```
- **404 Not Found:** Abonnement non trouvé.

#### `GET /api/subscriptions/current/`

**Description:** Récupère l'abonnement actif actuel de l'utilisateur authentifié.

**Réponses (JSON):**
- **200 OK:** Abonnement actuel.
  ```json
  {
    "id": 1,
    "plan": { "id": 1, "nom": "Standard" },
    "statut": "ACTIF",
    "days_remaining": 15
  }
  ```
- **404 Not Found:** Aucun abonnement actif.

### 5.3. Actions sur les Abonnements

#### `POST /api/subscriptions/renew/`

**Description:** Renouvelle l'abonnement actif de l'utilisateur.

**Réponses (JSON):**
- **200 OK:** Abonnement renouvelé avec succès.
  ```json
  {
    "message": "Abonnement renouvelé avec succès.",
    "new_end_date": "2024-08-31T23:59:59Z"
  }
  ```
- **400 Bad Request:** Aucun abonnement actif ou erreur de renouvellement.

#### `POST /api/subscriptions/cancel/`

**Description:** Annule l'abonnement actif de l'utilisateur.

**Réponses (JSON):**
- **200 OK:** Abonnement annulé avec succès.
  ```json
  {
    "message": "Abonnement annulé avec succès."
  }
  ```
- **400 Bad Request:** Aucun abonnement actif ou erreur d'annulation.

#### `POST /api/subscriptions/upgrade/`

**Description:** Met à niveau l'abonnement de l'utilisateur vers un plan supérieur.

**Corps de la requête (JSON):**
```json
{
  "new_plan_id": 2 // ID du nouveau plan (ex: Premium)
}
```

**Réponses (JSON):**
- **200 OK:** Abonnement mis à niveau avec succès.
  ```json
  {
    "message": "Abonnement mis à niveau avec succès.",
    "new_plan": { "id": 2, "nom": "Premium" }
  }
  ```
- **400 Bad Request:** Plan invalide ou impossible de mettre à niveau.

#### `POST /api/subscriptions/pay/`

**Description:** Initie le paiement pour un nouvel abonnement ou un renouvellement.

**Corps de la requête (JSON):**
```json
{
  "plan_id": 1,
  "payment_method": "MOMO_MTN",
  "phone_number": "+22997000000"
}
```

**Réponses (JSON):**
- **201 Created:** Paiement initié. Le statut du paiement sera `EN_ATTENTE`.
  ```json
  {
    "message": "Paiement d'abonnement initié. Veuillez confirmer sur votre téléphone.",
    "payment_uuid": "<uuid_du_paiement>"
  }
  ```
- **400 Bad Request:** Plan invalide ou erreur de paiement.

### 5.4. Informations et Statistiques

#### `GET /api/subscriptions/usage/`

**Description:** Récupère l'utilisation actuelle de l'abonnement de l'utilisateur (ex: événements créés ce mois).

**Réponses (JSON):**
- **200 OK:** Utilisation de l'abonnement.
  ```json
  {
    "evenements_crees_ce_mois": 2,
    "max_evenements_par_mois": 5,
    "days_remaining": 15
  }
  ```

#### `GET /api/subscriptions/benefits/`

**Description:** Récupère la liste des avantages du plan d'abonnement actuel de l'utilisateur.

**Réponses (JSON):**
- **200 OK:** Avantages de l'abonnement.
  ```json
  [
    {
      "nom": "Support prioritaire",
      "description": "Accès direct à notre équipe de support.",
      "inclus": true
    }
  ]
  ```

#### `GET /api/subscriptions/history/`

**Description:** Récupère l'historique des changements d'abonnement de l'utilisateur.

**Réponses (JSON):**
- **200 OK:** Historique des abonnements.
  ```json
  [
    {
      "id": 1,
      "action": "SOUSCRIPTION",
      "plan_nom": "Standard",
      "date_action": "2024-07-01T00:00:00Z"
    }
  ]
  ```

#### `GET /api/subscriptions/stats/`

**Description:** Récupère les statistiques générales sur les abonnements (pour les administrateurs).

**Réponses (JSON):**
- **200 OK:** Statistiques abonnements.
  ```json
  {
    "total_subscriptions": 250,
    "active_subscriptions": 200,
    "expired_subscriptions": 50,
    "revenue_from_subscriptions": 10000000 // FCFA
  }
  ```

### 5.5. Webhooks

#### `POST /api/subscriptions/activate-webhook/`

**Description:** Endpoint pour activer un abonnement via un webhook externe (ex: après confirmation de paiement).

**Corps de la requête (JSON):**
```json
{
  "payment_uuid": "<uuid_du_paiement>",
  "status": "success",
  "transaction_id": "<id_transaction_externe>"
}
```

**Réponses (JSON):**
- **200 OK:** Abonnement activé/mis à jour.
  ```json
  {
    "message": "Abonnement mis à jour via webhook."
  }
  ```
- **400 Bad Request:** Données invalides ou paiement non trouvé.

## 6. Application `payments`

L'application `payments` gère toutes les transactions financières, y compris les paiements, les remboursements, les commissions et les transactions Mobile Money. Elle assure le suivi et la validation des flux d'argent au sein de la plateforme.

### 6.1. Paiements

#### `GET /api/payments/`

**Description:** Récupère la liste de tous les paiements effectués par l'utilisateur authentifié.

**Réponses (JSON):**
- **200 OK:** Liste des paiements.
  ```json
  [
    {
      "uuid": "<uuid_paiement>",
      "type_paiement": "BILLET",
      "montant": "5000.00",
      "statut": "REUSSI",
      "date_creation": "2024-07-29T14:30:00Z"
    }
  ]
  ```

#### `POST /api/payments/initiate/`

**Description:** Initie un nouveau paiement. Ce endpoint est générique et peut être utilisé pour différents types de paiements (abonnements, billets).

**Corps de la requête (JSON):**
```json
{
  "type_paiement": "ABONNEMENT", // ou "BILLET"
  "montant": 10000,
  "methode_paiement": "MOMO_MTN",
  "telephone_paiement": "+22997000000",
  "subscription_id": 1, // Optionnel, si paiement d'abonnement
  "event_ticket_id": 1 // Optionnel, si paiement de billet
}
```

**Réponses (JSON):**
- **201 Created:** Paiement initié. Le statut sera `EN_ATTENTE`.
  ```json
  {
    "message": "Paiement initié. Veuillez confirmer sur votre téléphone.",
    "payment_uuid": "<uuid_du_paiement>"
  }
  ```
- **400 Bad Request:** Données invalides.

#### `GET /api/payments/<uuid:uuid>/`

**Description:** Récupère les détails d'un paiement spécifique par son UUID.

**Paramètres de l'URL:**
- `uuid`: L'UUID du paiement.

**Réponses (JSON):**
- **200 OK:** Détails du paiement.
  ```json
  {
    "uuid": "<uuid_paiement>",
    "utilisateur": { "id": 1, "username": "utilisateur" },
    "type_paiement": "BILLET",
    "montant": "5000.00",
    "frais": "500.00",
    "montant_net": "4500.00",
    "statut": "REUSSI",
    "methode_paiement": "MOMO_MTN",
    "date_creation": "2024-07-29T14:30:00Z"
  }
  ```
- **404 Not Found:** Paiement non trouvé.

#### `POST /api/payments/verify/`

**Description:** Vérifie le statut d'un paiement après une tentative.

**Corps de la requête (JSON):**
```json
{
  "payment_uuid": "<uuid_du_paiement>"
}
```

**Réponses (JSON):**
- **200 OK:** Statut du paiement.
  ```json
  {
    "payment_uuid": "<uuid_du_paiement>",
    "status": "REUSSI", // ou "EN_ATTENTE", "ECHEC"
    "message": "Paiement confirmé avec succès."
  }
  ```
- **400 Bad Request:** UUID invalide.

#### `POST /api/payments/cancel/`

**Description:** Annule un paiement en attente.

**Corps de la requête (JSON):**
```json
{
  "payment_uuid": "<uuid_du_paiement>"
}
```

**Réponses (JSON):**
- **200 OK:** Paiement annulé.
  ```json
  {
    "message": "Paiement annulé avec succès."
  }
  ```
- **400 Bad Request:** Paiement non annulable ou UUID invalide.

#### `POST /api/payments/retry/`

**Description:** Retente un paiement qui a échoué ou est en attente.

**Corps de la requête (JSON):**
```json
{
  "payment_uuid": "<uuid_du_paiement>"
}
```

**Réponses (JSON):**
- **200 OK:** Retentative de paiement initiée.
  ```json
  {
    "message": "Retentative de paiement initiée."
  }
  ```
- **400 Bad Request:** Paiement non retentable ou UUID invalide.

### 6.2. Remboursements

#### `GET /api/payments/refunds/`

**Description:** Récupère la liste des demandes de remboursement de l'utilisateur authentifié.

**Réponses (JSON):**
- **200 OK:** Liste des remboursements.
  ```json
  [
    {
      "id": 1,
      "payment_original_uuid": "<uuid_paiement_original>",
      "montant_remboursement": "4500.00",
      "statut": "DEMANDE",
      "date_demande": "2024-07-30T10:00:00Z"
    }
  ]
  ```

#### `GET /api/payments/refunds/<int:pk>/`

**Description:** Récupère les détails d'une demande de remboursement spécifique.

**Paramètres de l'URL:**
- `pk`: L'ID de la demande de remboursement.

**Réponses (JSON):**
- **200 OK:** Détails du remboursement.
  ```json
  {
    "id": 1,
    "payment_original": { "uuid": "<uuid_paiement_original>", "montant": "5000.00" },
    "demandeur": { "id": 1, "username": "utilisateur" },
    "montant_remboursement": "4500.00",
    "raison": "ANNULATION_EVENT",
    "description": "Événement annulé par l'organisateur.",
    "statut": "DEMANDE",
    "date_demande": "2024-07-30T10:00:00Z"
  }
  ```
- **404 Not Found:** Remboursement non trouvé.

### 6.3. Statistiques et Informations de Paiement

#### `GET /api/payments/stats/`

**Description:** Récupère les statistiques générales sur les paiements (pour les administrateurs).

**Réponses (JSON):**
- **200 OK:** Statistiques paiements.
  ```json
  {
    "total_payments": 1000,
    "successful_payments": 950,
    "total_revenue": 25000000 // FCFA
  }
  ```

#### `GET /api/payments/methods/`

**Description:** Récupère la liste des méthodes de paiement supportées.

**Réponses (JSON):**
- **200 OK:** Méthodes de paiement.
  ```json
  [
    {
      "code": "MOMO_MTN",
      "name": "Mobile Money MTN",
      "active": true
    },
    {
      "code": "CARTE_BANCAIRE",
      "name": "Carte bancaire",
      "active": false
    }
  ]
  ```

#### `GET /api/payments/summary/`

**Description:** Récupère un résumé des paiements de l'utilisateur authentifié.

**Réponses (JSON):**
- **200 OK:** Résumé des paiements.
  ```json
  {
    "total_spent": "50000.00",
    "last_payment_date": "2024-07-29T14:30:00Z",
    "pending_payments_count": 2
  }
  ```

### 6.4. Transactions et Commissions

#### `GET /api/payments/transactions/`

**Description:** Récupère la liste des transactions Mobile Money (pour les administrateurs).

**Réponses (JSON):**
- **200 OK:** Liste des transactions Mobile Money.
  ```json
  [
    {
      "id": 1,
      "payment_uuid": "<uuid_paiement>",
      "operateur": "MTN",
      "numero_telephone": "+22997000000",
      "transaction_id": "TRX12345",
      "date_initiation": "2024-07-29T14:30:00Z"
    }
  ]
  ```

#### `GET /api/payments/commissions/`

**Description:** Récupère la liste des commissions perçues par la plateforme (pour les administrateurs).

**Réponses (JSON):**
- **200 OK:** Liste des commissions.
  ```json
  [
    {
      "id": 1,
      "type_commission": "BILLETTERIE",
      "montant_commission": "500.00",
      "statut": "CALCULEE",
      "event_titre": "Concert de Rock"
    }
  ]
  ```

### 6.5. Webhooks Mobile Money

#### `POST /api/payments/webhooks/orange/`

**Description:** Endpoint pour les webhooks de confirmation de paiement Orange Money.

**Corps de la requête (JSON):**
```json
{ /* Données spécifiques au webhook Orange Money */ }
```

**Réponses (JSON):**
- **200 OK:** Webhook traité.

#### `POST /api/payments/webhooks/mtn/`

**Description:** Endpoint pour les webhooks de confirmation de paiement MTN Money.

**Corps de la requête (JSON):**
```json
{ /* Données spécifiques au webhook MTN Money */ }
```

**Réponses (JSON):**
- **200 OK:** Webhook traité.

#### `POST /api/payments/webhooks/moov/`

**Description:** Endpoint pour les webhooks de confirmation de paiement Moov Money.

**Corps de la requête (JSON):**
```json
{ /* Données spécifiques au webhook Moov Money */ }
```

**Réponses (JSON):**
- **200 OK:** Webhook traité.

## 7. Application `notifications`

L'application `notifications` gère l'envoi, la réception et la gestion des notifications pour les utilisateurs. Elle inclut la gestion des templates, des préférences et des tokens push.

### 7.1. Notifications

#### `GET /api/notifications/`

**Description:** Récupère la liste des notifications de l'utilisateur authentifié.

**Réponses (JSON):**
- **200 OK:** Liste des notifications.
  ```json
  [
    {
      "id": 1,
      "titre": "Nouvel événement près de chez vous",
      "message": "Un concert de jazz est prévu le 15 août.",
      "type_notification": "EVENT_REMINDER",
      "statut": "ENVOYE",
      "date_creation": "2024-07-28T10:00:00Z",
      "is_read": false
    }
  ]
  ```

#### `GET /api/notifications/<int:pk>/`

**Description:** Récupère les détails d'une notification spécifique.

**Paramètres de l'URL:**
- `pk`: L'ID de la notification.

**Réponses (JSON):**
- **200 OK:** Détails de la notification.
  ```json
  {
    "id": 1,
    "titre": "Nouvel événement près de chez vous",
    "message": "Un concert de jazz est prévu le 15 août.",
    "type_notification": "EVENT_REMINDER",
    "statut": "ENVOYE",
    "date_creation": "2024-07-28T10:00:00Z",
    "date_lecture": null,
    "lien_action": "/events/1",
    "donnees_supplementaires": { "event_id": 1 }
  }
  ```
- **404 Not Found:** Notification non trouvée.

#### `POST /api/notifications/mark-read/`

**Description:** Marque une ou plusieurs notifications comme lues.

**Corps de la requête (JSON):**
```json
{
  "notification_ids": [1, 2, 3] // Liste des IDs de notifications à marquer comme lues
}
```

**Réponses (JSON):**
- **200 OK:** Notifications marquées comme lues.
  ```json
  {
    "message": "Notifications marquées comme lues."
  }
  ```

#### `POST /api/notifications/mark-all-read/`

**Description:** Marque toutes les notifications non lues de l'utilisateur comme lues.

**Réponses (JSON):**
- **200 OK:** Toutes les notifications marquées comme lues.
  ```json
  {
    "message": "Toutes les notifications ont été marquées comme lues."
  }
  ```

#### `GET /api/notifications/stats/`

**Description:** Récupère les statistiques de notification de l'utilisateur (nombre total, lues, non lues).

**Réponses (JSON):**
- **200 OK:** Statistiques de notification.
  ```json
  {
    "total_notifications": 10,
    "read_notifications": 7,
    "unread_notifications": 3
  }
  ```

#### `GET /api/notifications/unread-count/`

**Description:** Récupère le nombre de notifications non lues de l'utilisateur.

**Réponses (JSON):**
- **200 OK:** Nombre de notifications non lues.
  ```json
  {
    "unread_count": 3
  }
  ```

#### `POST /api/notifications/test/`

**Description:** Envoie une notification de test à l'utilisateur authentifié.

**Réponses (JSON):**
- **200 OK:** Notification de test envoyée.
  ```json
  {
    "message": "Notification de test envoyée."
  }
  ```

#### `DELETE /api/notifications/<int:notification_id>/delete/`

**Description:** Supprime une notification spécifique.

**Paramètres de l'URL:**
- `notification_id`: L'ID de la notification à supprimer.

**Réponses (JSON):**
- **204 No Content:** Notification supprimée avec succès.
- **404 Not Found:** Notification non trouvée.

### 7.2. Préférences de Notification

#### `GET /api/notifications/preferences/`

**Description:** Récupère les préférences de notification de l'utilisateur authentifié.

**Réponses (JSON):**
- **200 OK:** Préférences de notification.
  ```json
  [
    {
      "type_notification": "EVENT_REMINDER",
      "canal": "EMAIL",
      "actif": true,
      "frequence": "IMMEDIATE"
    }
  ]
  ```

#### `PUT /api/notifications/preferences/`

**Description:** Met à jour les préférences de notification de l'utilisateur.

**Corps de la requête (JSON):**
```json
{
  "type_notification": "EVENT_REMINDER",
  "canal": "EMAIL",
  "actif": false,
  "frequence": "JAMAIS"
}
```

**Réponses (JSON):**
- **200 OK:** Préférences mises à jour.
  ```json
  {
    "message": "Préférences de notification mises à jour."
  }
  ```
- **400 Bad Request:** Données invalides.

### 7.3. Templates de Notification

#### `GET /api/notifications/templates/`

**Description:** Récupère la liste de tous les templates de notification disponibles (pour les administrateurs).

**Réponses (JSON):**
- **200 OK:** Liste des templates.
  ```json
  [
    {
      "id": 1,
      "type_notification": "WELCOME",
      "nom": "Message de bienvenue",
      "canaux_actifs": ["EMAIL", "IN_APP"]
    }
  ]
  ```

### 7.4. Push Tokens

#### `GET /api/notifications/push-tokens/`

**Description:** Récupère la liste des tokens push enregistrés pour l'utilisateur authentifié.

**Réponses (JSON):**
- **200 OK:** Liste des tokens push.
  ```json
  [
    {
      "id": 1,
      "token": "<token_push_appareil>",
      "plateforme": "ANDROID",
      "nom_appareil": "Mon Téléphone"
    }
  ]
  ```

#### `POST /api/notifications/push-tokens/`

**Description:** Enregistre un nouveau token push pour l'utilisateur.

**Corps de la requête (JSON):**
```json
{
  "token": "<nouveau_token_push>",
  "plateforme": "ANDROID",
  "nom_appareil": "Mon Nouveau Téléphone"
}
```

**Réponses (JSON):**
- **201 Created:** Token push enregistré.
  ```json
  {
    "message": "Token push enregistré avec succès."
  }
  ```
- **400 Bad Request:** Token déjà enregistré ou données invalides.

### 7.5. Actions Administratives

#### `POST /api/notifications/bulk-send/`

**Description:** Envoie une notification en masse à un groupe d'utilisateurs (pour les administrateurs).

**Corps de la requête (JSON):**
```json
{
  "template_id": 1, // ID du template à utiliser
  "target_users": [1, 2, 3], // Liste des IDs d'utilisateurs
  "additional_data": { "promo_code": "SUMMER2024" }
}
```

**Réponses (JSON):**
- **200 OK:** Envoi en masse initié.
  ```json
  {
    "message": "Envoi de notifications en masse initié."
  }
  ```
- **400 Bad Request:** Données invalides.

## 8. Application `admin_dashboard`

L'application `admin_dashboard` fournit des endpoints pour la gestion et la surveillance du système par les administrateurs. Elle offre des statistiques, des outils de gestion des utilisateurs et des événements, ainsi que des informations sur la santé du système.

### 8.1. Dashboard Principal

#### `GET /api/admin/dashboard/`

**Description:** Récupère un aperçu général des statistiques clés du système pour le tableau de bord administrateur.

**Réponses (JSON):**
- **200 OK:** Aperçu du tableau de bord.
  ```json
  {
    "total_users": 1500,
    "active_users": 1200,
    "total_events": 500,
    "pending_events": 50,
    "total_revenue": 15000000,
    "active_subscriptions": 250,
    "new_registrations_today": 15
  }
  ```

### 8.2. Statistiques

#### `GET /api/admin/stats/users/`

**Description:** Récupère des statistiques détaillées sur les utilisateurs (croissance, démographie, activité).

**Réponses (JSON):**
- **200 OK:** Statistiques utilisateurs.
  ```json
  {
    "total_users": 1500,
    "verified_users": 800,
    "unverified_users": 700,
    "users_by_country": { "Benin": 1000, "Togo": 200 },
    "registrations_last_30_days": [ /* ... données journalières ... */ ]
  }
  ```

#### `GET /api/admin/stats/events/`

**Description:** Récupère des statistiques détaillées sur les événements (création, participation, revenus).

**Réponses (JSON):**
- **200 OK:** Statistiques événements.
  ```json
  {
    "total_events": 500,
    "events_by_category": { "Concert": 150, "Conférence": 100 },
    "total_tickets_sold": 2000,
    "revenue_from_tickets": 10000000,
    "events_last_30_days": [ /* ... données journalières ... */ ]
  }
  ```

#### `GET /api/admin/stats/payments/`

**Description:** Récupère des statistiques détaillées sur les paiements et les revenus.

**Réponses (JSON):**
- **200 OK:** Statistiques paiements.
  ```json
  {
    "total_transactions": 1200,
    "successful_transactions": 1150,
    "failed_transactions": 50,
    "total_revenue": 25000000,
    "revenue_by_month": [ /* ... données mensuelles ... */ ]
  }
  ```

### 8.3. Santé du Système

#### `GET /api/admin/system/health/`

**Description:** Vérifie l'état de santé détaillé des composants du système (base de données, Redis, Celery, etc.).

**Réponses (JSON):**
- **200 OK:** État de santé du système.
  ```json
  {
    "overall_status": "OK",
    "database": { "status": "connected", "latency_ms": 10 },
    "redis": { "status": "connected" },
    "celery_workers": { "status": "active", "count": 3 }
  }
  ```

### 8.4. Actions Administratives

#### `GET /api/admin/actions/`

**Description:** Récupère la liste des actions administratives récentes (logs d'audit).

**Réponses (JSON):**
- **200 OK:** Liste des actions administratives.
  ```json
  [
    {
      "id": 1,
      "admin_user": "admin_user",
      "action": "APPROVE",
      "description": "Approbation de l'événement 'Concert de Rock'",
      "date_action": "2024-07-29T15:00:00Z"
    }
  ]
  ```

#### `POST /api/admin/bulk-action/`

**Description:** Exécute une action en masse sur plusieurs objets (ex: approuver plusieurs événements).

**Corps de la requête (JSON):**
```json
{
  "action_type": "approve_events",
  "object_ids": [1, 2, 3],
  "reason": "Conforme aux directives"
}
```

**Réponses (JSON):**
- **200 OK:** Action en masse exécutée.
  ```json
  {
    "message": "Action en masse exécutée avec succès.",
    "processed_count": 3
  }
  ```
- **400 Bad Request:** Action invalide ou objets non trouvés.

#### `POST /api/admin/quick-action/`

**Description:** Exécute une action rapide prédéfinie (ex: activer/désactiver le mode maintenance).

**Corps de la requête (JSON):**
```json
{
  "action_name": "toggle_maintenance_mode",
  "value": true,
  "message": "Maintenance système prévue."
}
```

**Réponses (JSON):**
- **200 OK:** Action rapide exécutée.
  ```json
  {
    "message": "Mode maintenance activé."
  }
  ```
- **400 Bad Request:** Action invalide.

### 8.5. Métriques

#### `GET /api/admin/metrics/`

**Description:** Récupère des métriques de performance et d'utilisation du système.

**Réponses (JSON):**
- **200 OK:** Métriques système.
  ```json
  {
    "cpu_usage": "25%",
    "memory_usage": "60%",
    "database_connections": 50,
    "api_request_rate_per_minute": 120
  }
  ```



