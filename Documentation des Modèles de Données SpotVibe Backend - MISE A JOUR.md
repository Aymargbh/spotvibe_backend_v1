# Documentation des Modèles de Données SpotVibe Backend - VERSION MISE À JOUR

Ce document détaille la structure complète et mise à jour des modèles de données utilisés dans le backend de SpotVibe. Il inclut tous les nouveaux modèles ajoutés et les modifications apportées aux modèles existants.

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

### 1.1. `SocialAccount`
Modèle pour les comptes de réseaux sociaux liés (Google, Facebook).

| Champ               | Type de Donnée | Description                                        |
|---------------------|----------------|----------------------------------------------------|
| `utilisateur`       | ForeignKey     | Utilisateur propriétaire du compte social (vers `User`) |
| `provider`          | CharField      | Fournisseur du compte social (GOOGLE, FACEBOOK)   |
| `social_id`         | CharField      | Identifiant unique chez le fournisseur             |
| `email`             | EmailField     | Email associé au compte social                     |
| `nom_complet`       | CharField      | Nom complet récupéré du compte social              |
| `photo_url`         | URLField       | URL de la photo de profil                          |
| `access_token`      | TextField      | Token d'accès pour l'API du fournisseur            |
| `refresh_token`     | TextField      | Token de rafraîchissement                          |
| `token_expires_at`  | DateTimeField  | Date d'expiration du token d'accès                 |
| `date_creation`     | DateTimeField  | Date de liaison du compte                          |
| `date_modification` | DateTimeField  | Date de dernière modification                      |
| `derniere_utilisation`| DateTimeField  | Dernière utilisation pour la connexion             |
| `actif`             | BooleanField   | Compte social actif                                |

### 1.2. `LoginAttempt`
Modèle pour les tentatives de connexion.

| Champ               | Type de Donnée | Description                                        |
|---------------------|----------------|----------------------------------------------------|
| `utilisateur`       | ForeignKey     | Utilisateur concerné (si existant) (vers `User`) |
| `email_tente`       | EmailField     | Email utilisé pour la tentative                    |
| `statut`            | CharField      | Résultat (REUSSI, ECHEC, BLOQUE)                  |
| `raison_echec`      | CharField      | Raison de l'échec de connexion                     |
| `adresse_ip`        | GenericIPAddressField | Adresse IP de la tentative                         |
| `user_agent`        | TextField      | User Agent du navigateur                           |
| `pays`              | CharField      | Pays d'origine de l'IP                             |
| `ville`             | CharField      | Ville d'origine de l'IP                            |
| `date_tentative`    | DateTimeField  | Date et heure de la tentative                      |
| `duree_session`     | DurationField  | Durée de la session (pour les connexions réussies) |

### 1.3. `PasswordReset`
Modèle pour les demandes de réinitialisation de mot de passe.

| Champ               | Type de Donnée | Description                                        |
|---------------------|----------------|----------------------------------------------------|
| `utilisateur`       | ForeignKey     | Utilisateur demandant la réinitialisation (vers `User`) |
| `token`             | CharField      | Token de réinitialisation                          |
| `statut`            | CharField      | Statut (ACTIF, UTILISE, EXPIRE, ANNULE)           |
| `date_creation`     | DateTimeField  | Date de création du token                          |
| `date_expiration`   | DateTimeField  | Date d'expiration du token                         |
| `date_utilisation`  | DateTimeField  | Date d'utilisation du token                        |
| `adresse_ip_creation`| GenericIPAddressField | IP utilisée pour créer le token                    |
| `adresse_ip_utilisation`| GenericIPAddressField | IP utilisée pour utiliser le token                 |

### 1.4. `TwoFactorAuth`
Modèle pour l'authentification à deux facteurs.

| Champ               | Type de Donnée | Description                                        |
|---------------------|----------------|----------------------------------------------------|
| `utilisateur`       | OneToOneField  | Utilisateur concerné (vers `User`)               |
| `actif`             | BooleanField   | Authentification 2FA activée                       |
| `methode`           | CharField      | Méthode (SMS, EMAIL, TOTP)                         |
| `secret_key`        | CharField      | Clé secrète pour TOTP                              |
| `codes_recuperation`| JSONField      | Codes de récupération d'urgence                    |
| `derniere_utilisation`| DateTimeField  | Dernière utilisation de 2FA                        |
| `date_activation`   | DateTimeField  | Date d'activation de 2FA                           |

---

## 2. Application `users`

### 2.1. `User`
Modèle utilisateur personnalisé pour SpotVibe, étendant `AbstractUser`.

| Champ                   | Type de Donnée | Description                                        |
|-------------------------|----------------|----------------------------------------------------|
| `username`              | CharField      | Nom d'utilisateur unique                           |
| `email`                 | EmailField     | Adresse email unique                               |
| `first_name`            | CharField      | Prénom                                             |
| `last_name`             | CharField      | Nom de famille                                     |
| `telephone`             | CharField      | Numéro de téléphone (+229XXXXXXXX)                |
| `date_naissance`        | DateField      | Date de naissance                                  |
| `photo_profil`          | ImageField     | Photo de profil (max 5MB)                         |
| `bio`                   | TextField      | Description courte de l'utilisateur                |
| `est_verifie`           | BooleanField   | Compte vérifié par l'administration                |
| `date_verification`     | DateTimeField  | Date de vérification du compte                     |
| `notifications_email`   | BooleanField   | Recevoir les notifications par email               |
| `notifications_push`    | BooleanField   | Recevoir les notifications push                    |
| `date_creation`         | DateTimeField  | Date de création du compte                         |
| `is_active`             | BooleanField   | Compte actif                                       |
| `is_staff`              | BooleanField   | Membre du staff                                    |
| `is_superuser`          | BooleanField   | Super utilisateur                                  |

**Méthodes importantes:**
- `get_events_count()`: Nombre d'événements créés
- `get_participations_count()`: Nombre de participations
- `get_followers_count()`: Nombre de followers
- `get_following_count()`: Nombre de personnes suivies

### 2.2. `Entity`
Modèle pour les entités/organisations.

| Champ                   | Type de Donnée | Description                                        |
|-------------------------|----------------|----------------------------------------------------|
| `proprietaire`          | ForeignKey     | Utilisateur propriétaire (vers `User`)            |
| `nom`                   | CharField      | Nom de l'entité                                   |
| `type_entite`           | CharField      | Type (ENTREPRISE, ASSOCIATION, GOUVERNEMENT, etc.) |
| `description`           | TextField      | Description de l'entité                           |
| `adresse`               | TextField      | Adresse physique                                   |
| `telephone`             | CharField      | Numéro de téléphone                               |
| `email`                 | EmailField     | Email de contact                                   |
| `site_web`              | URLField       | Site web officiel                                  |
| `logo`                  | ImageField     | Logo de l'entité                                   |
| `numero_enregistrement` | CharField      | Numéro d'enregistrement officiel                  |
| `est_verifie`           | BooleanField   | Entité vérifiée                                   |
| `date_verification`     | DateTimeField  | Date de vérification                               |
| `actif`                 | BooleanField   | Entité active                                      |
| `date_creation`         | DateTimeField  | Date de création                                   |

### 2.3. `UserVerification`
Modèle pour les demandes de vérification d'identité.

| Champ                   | Type de Donnée | Description                                        |
|-------------------------|----------------|----------------------------------------------------|
| `utilisateur`           | ForeignKey     | Utilisateur demandant la vérification (vers `User`) |
| `statut`                | CharField      | Statut (EN_ATTENTE, APPROUVE, REJETE, EXPIRE)     |
| `document_identite`     | FileField      | Document d'identité scanné                        |
| `document_selfie`       | ImageField     | Selfie avec le document                            |
| `date_soumission`       | DateTimeField  | Date de soumission                                 |
| `date_validation`       | DateTimeField  | Date de validation/rejet                           |
| `commentaire_admin`     | TextField      | Commentaire de l'administrateur                    |

### 2.4. `Follow`
Modèle pour les relations de suivi entre utilisateurs.

| Champ                   | Type de Donnée | Description                                        |
|-------------------------|----------------|----------------------------------------------------|
| `follower`              | ForeignKey     | Utilisateur qui suit (vers `User`)                |
| `following`             | ForeignKey     | Utilisateur suivi (vers `User`)                   |
| `date_suivi`            | DateTimeField  | Date de début du suivi                             |
| `notifications_activees`| BooleanField   | Recevoir les notifications de cet utilisateur     |

---

## 3. Application `events`

### 3.1. `EventCategory`
Modèle pour les catégories d'événements.

| Champ                   | Type de Donnée | Description                                        |
|-------------------------|----------------|----------------------------------------------------|
| `nom`                   | CharField      | Nom de la catégorie                                |
| `description`           | TextField      | Description de la catégorie                        |
| `icone`                 | CharField      | Nom de l'icône (ex: fas fa-music)                 |
| `couleur`               | CharField      | Couleur hexadécimale                               |
| `ordre`                 | PositiveIntegerField | Ordre d'affichage                                  |
| `actif`                 | BooleanField   | Catégorie active                                   |

### 3.2. `EventMedia`
Modèle pour gérer les médias (images et vidéos) des événements.

| Champ                   | Type de Donnée | Description                                        |
|-------------------------|----------------|----------------------------------------------------|
| `evenement`             | ForeignKey     | Événement associé (vers `Event`)                  |
| `fichier`               | FileField      | Fichier média (image ou vidéo)                    |
| `type_media`            | CharField      | Type (image, video)                                |
| `usage`                 | CharField      | Usage (galerie, couverture, post_cover, thumbnail) |
| `titre`                 | CharField      | Titre du média                                     |
| `description`           | TextField      | Description du média                               |
| `ordre`                 | PositiveIntegerField | Ordre d'affichage                                  |
| `thumbnail`             | ImageField     | Miniature (générée automatiquement pour les vidéos) |
| `largeur`               | PositiveIntegerField | Largeur en pixels                                  |
| `hauteur`               | PositiveIntegerField | Hauteur en pixels                                  |
| `duree`                 | DurationField  | Durée (pour les vidéos)                            |
| `taille_fichier`        | PositiveIntegerField | Taille du fichier en octets                       |
| `uploade_par`           | ForeignKey     | Utilisateur qui a uploadé (vers `User`)           |
| `date_upload`           | DateTimeField  | Date d'upload                                      |
| `est_active`            | BooleanField   | Média actif                                        |

### 3.3. `Event`
Modèle principal pour les événements.

| Champ                   | Type de Donnée | Description                                        |
|-------------------------|----------------|----------------------------------------------------|
| `titre`                 | CharField      | Titre de l'événement                               |
| `description`           | TextField      | Description détaillée                              |
| `description_courte`    | CharField      | Résumé court pour les listes                      |
| `date_debut`            | DateTimeField  | Date et heure de début                             |
| `date_fin`              | DateTimeField  | Date et heure de fin                               |
| `lieu`                  | CharField      | Nom du lieu                                        |
| `adresse`               | TextField      | Adresse complète                                   |
| `latitude`              | DecimalField   | Coordonnée latitude                                |
| `longitude`             | DecimalField   | Coordonnée longitude                               |
| `lien_google_maps`      | URLField       | Lien vers Google Maps                              |
| `createur`              | ForeignKey     | Utilisateur créateur (vers `User`)                |
| `entite_organisatrice`  | ForeignKey     | Entité organisatrice (vers `Entity`)              |
| `categorie`             | ForeignKey     | Catégorie (vers `EventCategory`)                  |
| `type_acces`            | CharField      | Type d'accès (GRATUIT, PAYANT, INVITATION)        |
| `prix`                  | DecimalField   | Prix d'entrée en FCFA                             |
| `capacite_max`          | PositiveIntegerField | Nombre maximum de participants                     |
| `statut`                | CharField      | Statut (BROUILLON, EN_ATTENTE, VALIDE, REJETE, ANNULE, TERMINE) |
| `date_validation`       | DateTimeField  | Date de validation                                 |
| `validateur`            | ForeignKey     | Administrateur validateur (vers `User`)           |
| `commentaire_validation`| TextField      | Commentaire de validation                          |
| `nombre_vues`           | PositiveIntegerField | Nombre de vues                                     |
| `nombre_partages`       | PositiveIntegerField | Nombre de partages                                 |
| `date_creation`         | DateTimeField  | Date de création                                   |
| `date_modification`     | DateTimeField  | Date de modification                               |
| `billetterie_activee`   | BooleanField   | Système de billetterie activé                     |
| `lien_billetterie_externe`| URLField       | Lien vers billetterie externe                      |
| `commission_billetterie`| DecimalField   | Commission en pourcentage                          |

**Méthodes importantes:**
- `get_image_couverture()`: Image de couverture principale
- `get_post_cover_image()`: Image de couverture pour les posts
- `get_galerie_images()`: Images de la galerie
- `get_galerie_videos()`: Vidéos de la galerie
- `get_participants_count()`: Nombre de participants
- `get_interested_count()`: Nombre d'intéressés
- `is_full()`: Vérifier si l'événement est complet
- `can_participate(user)`: Vérifier si un utilisateur peut participer

### 3.4. `EventParticipation`
Modèle pour la participation aux événements.

| Champ                   | Type de Donnée | Description                                        |
|-------------------------|----------------|----------------------------------------------------|
| `utilisateur`           | ForeignKey     | Utilisateur participant (vers `User`)             |
| `evenement`             | ForeignKey     | Événement (vers `Event`)                          |
| `statut`                | CharField      | Statut (INTERESSE, PARTICIPE, A_PARTICIPE, ANNULE) |
| `date_participation`    | DateTimeField  | Date d'inscription                                 |
| `date_modification`     | DateTimeField  | Date de modification du statut                     |
| `commentaire`           | TextField      | Commentaire du participant                         |

### 3.5. `EventShare`
Modèle pour le partage d'événements.

| Champ                   | Type de Donnée | Description                                        |
|-------------------------|----------------|----------------------------------------------------|
| `utilisateur`           | ForeignKey     | Utilisateur qui partage (vers `User`)             |
| `evenement`             | ForeignKey     | Événement partagé (vers `Event`)                  |
| `plateforme`            | CharField      | Plateforme (FACEBOOK, TWITTER, INSTAGRAM, etc.)   |
| `date_partage`          | DateTimeField  | Date du partage                                    |
| `lien_genere`           | URLField       | Lien personnalisé généré                          |
| `nombre_clics`          | PositiveIntegerField | Nombre de clics sur le lien                       |

### 3.6. `EventTicket`
Modèle fusionné pour les catégories de billets et billets vendus.

| Champ                   | Type de Donnée | Description                                        |
|-------------------------|----------------|----------------------------------------------------|
| `evenement`             | ForeignKey     | Événement (vers `Event`)                          |
| `utilisateur`           | ForeignKey     | Acheteur du billet (vers `User`)                  |
| `nom`                   | CharField      | Nom de la catégorie de billet                     |
| `description`           | TextField      | Description de la catégorie                       |
| `prix`                  | DecimalField   | Prix unitaire en FCFA                             |
| `quantite_disponible`   | PositiveIntegerField | Nombre total disponible                           |
| `quantite_vendue`       | PositiveIntegerField | Nombre déjà vendu                                 |
| `date_debut_vente`      | DateTimeField  | Début des ventes                                  |
| `date_fin_vente`        | DateTimeField  | Fin des ventes                                     |
| `actif`                 | BooleanField   | Type de billet actif                               |
| `uuid`                  | UUIDField      | Identifiant unique du billet                      |
| `quantite`              | PositiveIntegerField | Quantité achetée                                   |
| `statut`                | CharField      | Statut (EN_ATTENTE, PAYE, ANNULE, REMBOURSE, UTILISE) |
| `code_qr`               | ImageField     | Code QR pour validation                            |
| `date_achat`            | DateTimeField  | Date d'achat                                       |
| `date_utilisation`      | DateTimeField  | Date d'utilisation                                 |
| `reference_paiement`    | CharField      | Référence du paiement                              |

**Méthodes importantes:**
- `disponible()`: Vérifier la disponibilité
- `get_total_price()`: Prix total
- `can_be_used()`: Vérifier si utilisable
- `generate_qr_code()`: Générer le code QR

---

## 4. Application `notifications`

### 4.1. `Notification`
Modèle principal pour les notifications.

| Champ                   | Type de Donnée | Description                                        |
|-------------------------|----------------|----------------------------------------------------|
| `destinataire`          | ForeignKey     | Utilisateur destinataire (vers `User`)            |
| `titre`                 | CharField      | Titre de la notification                           |
| `message`               | TextField      | Contenu de la notification                         |
| `type_notification`     | CharField      | Type (EVENEMENT, PAIEMENT, SYSTEME, etc.)         |
| `statut`                | CharField      | Statut (NOUVEAU, LU, ARCHIVE)                     |
| `canal`                 | CharField      | Canal (IN_APP, EMAIL, PUSH, SMS)                  |
| `donnees_supplementaires`| JSONField      | Données additionnelles                             |
| `lien_action`           | URLField       | Lien vers une action                               |
| `date_creation`         | DateTimeField  | Date de création                                   |
| `date_lecture`          | DateTimeField  | Date de lecture                                    |
| `date_expiration`       | DateTimeField  | Date d'expiration                                  |

### 4.2. `NotificationPreference`
Modèle pour les préférences de notifications.

| Champ                   | Type de Donnée | Description                                        |
|-------------------------|----------------|----------------------------------------------------|
| `utilisateur`           | OneToOneField  | Utilisateur (vers `User`)                         |
| `notifications_email`   | BooleanField   | Recevoir par email                                 |
| `notifications_push`    | BooleanField   | Recevoir les notifications push                    |
| `notifications_sms`     | BooleanField   | Recevoir par SMS                                   |
| `evenements_nouveaux`   | BooleanField   | Nouveaux événements                                |
| `evenements_rappels`    | BooleanField   | Rappels d'événements                               |
| `paiements_confirmations`| BooleanField   | Confirmations de paiement                          |
| `marketing`             | BooleanField   | Notifications marketing                            |
| `date_creation`         | DateTimeField  | Date de création                                   |
| `date_modification`     | DateTimeField  | Date de modification                               |

### 4.3. `NotificationTemplate`
Modèle pour les templates de notifications.

| Champ                   | Type de Donnée | Description                                        |
|-------------------------|----------------|----------------------------------------------------|
| `nom`                   | CharField      | Nom du template                                    |
| `type_notification`     | CharField      | Type de notification                               |
| `canal`                 | CharField      | Canal de diffusion                                 |
| `sujet`                 | CharField      | Sujet (pour email)                                 |
| `contenu`               | TextField      | Contenu du template                                |
| `variables`             | JSONField      | Variables disponibles                              |
| `actif`                 | BooleanField   | Template actif                                     |
| `date_creation`         | DateTimeField  | Date de création                                   |

### 4.4. `PushToken`
Modèle pour les tokens de notifications push.

| Champ                   | Type de Donnée | Description                                        |
|-------------------------|----------------|----------------------------------------------------|
| `utilisateur`           | ForeignKey     | Utilisateur (vers `User`)                         |
| `token`                 | CharField      | Token FCM/APNS                                     |
| `plateforme`            | CharField      | Plateforme (ANDROID, IOS, WEB)                    |
| `actif`                 | BooleanField   | Token actif                                        |
| `date_creation`         | DateTimeField  | Date d'enregistrement                              |
| `derniere_utilisation`  | DateTimeField  | Dernière utilisation                               |

---

## 5. Application `subscriptions`

### 5.1. `SubscriptionPlan`
Modèle pour les plans d'abonnement.

| Champ                   | Type de Donnée | Description                                        |
|-------------------------|----------------|----------------------------------------------------|
| `nom`                   | CharField      | Nom du plan                                        |
| `type_plan`             | CharField      | Type (STANDARD, PREMIUM, GOLD)                    |
| `prix`                  | DecimalField   | Prix en FCFA                                       |
| `duree`                 | CharField      | Durée (MENSUEL, TRIMESTRIEL, ANNUEL)              |
| `description`           | TextField      | Description du plan                                |
| `max_evenements_par_mois`| PositiveIntegerField | Limite d'événements par mois                      |
| `commission_reduite`    | DecimalField   | Taux de commission réduit                          |
| `support_prioritaire`   | BooleanField   | Support prioritaire                                |
| `analytics_avances`     | BooleanField   | Analytics avancés                                  |
| `promotion_evenements`  | BooleanField   | Promotion automatique                              |
| `personnalisation_profil`| BooleanField   | Personnalisation avancée                           |
| `actif`                 | BooleanField   | Plan disponible                                    |
| `ordre`                 | PositiveIntegerField | Ordre d'affichage                                  |
| `date_creation`         | DateTimeField  | Date de création                                   |

**Méthodes importantes:**
- `get_duration_days()`: Durée en jours
- `get_subscribers_count()`: Nombre d'abonnés actifs

### 5.2. `Subscription`
Modèle pour les abonnements des utilisateurs.

| Champ                   | Type de Donnée | Description                                        |
|-------------------------|----------------|----------------------------------------------------|
| `utilisateur`           | ForeignKey     | Utilisateur abonné (vers `User`)                  |
| `plan`                  | ForeignKey     | Plan souscrit (vers `SubscriptionPlan`)           |
| `date_debut`            | DateTimeField  | Date de début                                      |
| `date_fin`              | DateTimeField  | Date de fin                                        |
| `statut`                | CharField      | Statut (ACTIF, EXPIRE, ANNULE, SUSPENDU, EN_ATTENTE) |
| `prix_paye`             | DecimalField   | Prix effectivement payé                           |
| `renouvellement_automatique`| BooleanField   | Renouvellement automatique                         |
| `date_creation`         | DateTimeField  | Date de souscription                               |
| `reference_paiement`    | CharField      | Référence du paiement                              |
| `evenements_crees_ce_mois`| PositiveIntegerField | Événements créés ce mois                          |
| `derniere_reinitialisation_compteur`| DateTimeField | Dernière réinitialisation du compteur             |

**Méthodes importantes:**
- `is_active()`: Vérifier si actif
- `days_remaining()`: Jours restants
- `can_create_event()`: Peut créer un événement
- `increment_events_counter()`: Incrémenter le compteur
- `get_commission_rate()`: Taux de commission applicable

### 5.3. `SubscriptionFeature`
Modèle pour les fonctionnalités des plans.

| Champ                   | Type de Donnée | Description                                        |
|-------------------------|----------------|----------------------------------------------------|
| `plan`                  | ForeignKey     | Plan d'abonnement (vers `SubscriptionPlan`)       |
| `nom`                   | CharField      | Nom de la fonctionnalité                          |
| `description`           | TextField      | Description détaillée                              |
| `inclus`                | BooleanField   | Fonctionnalité incluse                             |
| `limite`                | CharField      | Limite de la fonctionnalité                       |
| `ordre`                 | PositiveIntegerField | Ordre d'affichage                                  |

### 5.4. `SubscriptionHistory`
Modèle pour l'historique des abonnements.

| Champ                   | Type de Donnée | Description                                        |
|-------------------------|----------------|----------------------------------------------------|
| `subscription`          | ForeignKey     | Abonnement (vers `Subscription`)                  |
| `action`                | CharField      | Action (SOUSCRIPTION, RENOUVELLEMENT, CHANGEMENT_PLAN, etc.) |
| `ancien_statut`         | CharField      | Statut avant l'action                              |
| `nouveau_statut`        | CharField      | Statut après l'action                              |
| `commentaire`           | TextField      | Commentaire sur l'action                           |
| `date_action`           | DateTimeField  | Date de l'action                                   |
| `utilisateur_action`    | ForeignKey     | Utilisateur qui a effectué l'action (vers `User`) |

---

## 6. Application `payments`

### 6.1. `Payment`
Modèle principal pour les paiements.

| Champ                   | Type de Donnée | Description                                        |
|-------------------------|----------------|----------------------------------------------------|
| `uuid`                  | UUIDField      | Identifiant unique                                 |
| `utilisateur`           | ForeignKey     | Utilisateur payeur (vers `User`)                  |
| `type_paiement`         | CharField      | Type (BILLET, ABONNEMENT, REMBOURSEMENT)          |
| `montant`               | DecimalField   | Montant en FCFA                                    |
| `devise`                | CharField      | Devise (FCFA par défaut)                           |
| `statut`                | CharField      | Statut (EN_ATTENTE, REUSSI, ECHEC, ANNULE, REMBOURSE) |
| `methode_paiement`      | CharField      | Méthode (MTN_MONEY, MOOV_MONEY, CARTE_BANCAIRE)   |
| `reference_externe`     | CharField      | Référence du fournisseur de paiement               |
| `reference_interne`     | CharField      | Référence interne                                  |
| `telephone_paiement`    | CharField      | Numéro de téléphone pour Mobile Money              |
| `description`           | TextField      | Description du paiement                            |
| `donnees_supplementaires`| JSONField      | Données additionnelles                             |
| `date_creation`         | DateTimeField  | Date de création                                   |
| `date_completion`       | DateTimeField  | Date de finalisation                               |
| `date_expiration`       | DateTimeField  | Date d'expiration                                  |

### 6.2. `Refund`
Modèle pour les remboursements.

| Champ                   | Type de Donnée | Description                                        |
|-------------------------|----------------|----------------------------------------------------|
| `paiement`              | ForeignKey     | Paiement original (vers `Payment`)                |
| `montant`               | DecimalField   | Montant remboursé                                  |
| `raison`                | CharField      | Raison du remboursement                            |
| `statut`                | CharField      | Statut (EN_ATTENTE, TRAITE, REJETE)               |
| `reference_remboursement`| CharField      | Référence du remboursement                         |
| `date_demande`          | DateTimeField  | Date de demande                                    |
| `date_traitement`       | DateTimeField  | Date de traitement                                 |
| `traite_par`            | ForeignKey     | Administrateur (vers `User`)                      |
| `commentaire_admin`     | TextField      | Commentaire administrateur                         |

### 6.3. `MomoTransaction`
Modèle pour les transactions Mobile Money.

| Champ                   | Type de Donnée | Description                                        |
|-------------------------|----------------|----------------------------------------------------|
| `paiement`              | ForeignKey     | Paiement associé (vers `Payment`)                 |
| `operateur`             | CharField      | Opérateur (MTN, MOOV)                             |
| `numero_telephone`      | CharField      | Numéro de téléphone                               |
| `reference_operateur`   | CharField      | Référence de l'opérateur                          |
| `statut_transaction`    | CharField      | Statut de la transaction                           |
| `code_erreur`           | CharField      | Code d'erreur si échec                            |
| `message_erreur`        | TextField      | Message d'erreur                                   |
| `date_initiation`       | DateTimeField  | Date d'initiation                                  |
| `date_completion`       | DateTimeField  | Date de finalisation                               |
| `donnees_callback`      | JSONField      | Données du callback                                |

### 6.4. `Commission`
Modèle pour les commissions.

| Champ                   | Type de Donnée | Description                                        |
|-------------------------|----------------|----------------------------------------------------|
| `paiement`              | ForeignKey     | Paiement source (vers `Payment`)                  |
| `evenement`             | ForeignKey     | Événement concerné (vers `Event`)                 |
| `montant_base`          | DecimalField   | Montant de base                                    |
| `taux_commission`       | DecimalField   | Taux de commission appliqué                        |
| `montant_commission`    | DecimalField   | Montant de la commission                           |
| `montant_organisateur`  | DecimalField   | Montant pour l'organisateur                       |
| `statut`                | CharField      | Statut (CALCULEE, VERSEE, EN_ATTENTE)             |
| `date_calcul`           | DateTimeField  | Date de calcul                                     |
| `date_versement`        | DateTimeField  | Date de versement                                  |

---

## 7. Application `admin_dashboard`

### 7.1. `AdminAction`
Modèle pour tracer les actions des administrateurs.

| Champ                   | Type de Donnée | Description                                        |
|-------------------------|----------------|----------------------------------------------------|
| `admin`                 | ForeignKey     | Administrateur (vers `User`)                      |
| `action`                | CharField      | Type d'action (APPROVE_EVENT, REJECT_EVENT, etc.) |
| `description`           | TextField      | Description détaillée                              |
| `content_type`          | ForeignKey     | Type d'objet concerné                              |
| `object_id`             | PositiveIntegerField | ID de l'objet concerné                             |
| `objet_concerne`        | GenericForeignKey | Objet concerné                                     |
| `date_action`           | DateTimeField  | Date et heure de l'action                          |
| `adresse_ip`            | GenericIPAddressField | Adresse IP                                         |
| `user_agent`            | TextField      | User Agent du navigateur                           |
| `session_key`           | CharField      | Clé de session                                     |
| `donnees_supplementaires`| JSONField      | Données supplémentaires                            |
| `validation_requise`    | BooleanField   | Action nécessitant validation                      |
| `validee_par`           | ForeignKey     | Administrateur validateur (vers `User`)           |
| `date_validation`       | DateTimeField  | Date de validation                                 |

**Méthodes importantes:**
- `validate_action(validator)`: Valider une action critique
- `cleanup_old_records(days)`: Nettoyer les anciens enregistrements
- `get_suspicious_activities(hours)`: Détecter les activités suspectes

### 7.2. `DashboardWidget`
Modèle pour les widgets configurables du dashboard.

| Champ                   | Type de Donnée | Description                                        |
|-------------------------|----------------|----------------------------------------------------|
| `nom`                   | CharField      | Nom du widget                                      |
| `type_widget`           | CharField      | Type (STATS, CHART, LIST, COUNTER, etc.)          |
| `titre`                 | CharField      | Titre affiché                                      |
| `description`           | TextField      | Description du widget                              |
| `configuration`         | JSONField      | Configuration JSON                                 |
| `requete_sql`           | TextField      | Requête SQL pour les données                       |
| `cache_duration`        | PositiveIntegerField | Durée de cache en secondes                         |
| `derniere_execution`    | DateTimeField  | Dernière exécution                                 |
| `resultats_cache`       | JSONField      | Résultats en cache                                 |
| `largeur`               | PositiveIntegerField | Largeur (1-12 colonnes)                           |
| `hauteur`               | PositiveIntegerField | Hauteur en pixels                                  |
| `ordre`                 | PositiveIntegerField | Ordre d'affichage                                  |
| `visible_pour`          | ManyToManyField | Utilisateurs autorisés (vers `User`)              |
| `groupes_autorises`     | ManyToManyField | Groupes autorisés                                  |
| `actif`                 | BooleanField   | Widget actif                                       |
| `createur`              | ForeignKey     | Créateur du widget (vers `User`)                  |

**Méthodes importantes:**
- `is_cache_valid()`: Vérifier la validité du cache
- `can_view(user)`: Vérifier les permissions de vue

---

## 8. Application `core`

### 8.1. `AppSettings`
Modèle pour les paramètres de configuration.

| Champ                   | Type de Donnée | Description                                        |
|-------------------------|----------------|----------------------------------------------------|
| `cle`                   | CharField      | Clé unique du paramètre                            |
| `valeur`                | TextField      | Valeur du paramètre                                |
| `type_valeur`           | CharField      | Type (STRING, INTEGER, FLOAT, BOOLEAN, JSON)      |
| `description`           | TextField      | Description du paramètre                           |
| `categorie`             | CharField      | Catégorie du paramètre                             |
| `modifiable`            | BooleanField   | Paramètre modifiable via l'interface              |
| `date_creation`         | DateTimeField  | Date de création                                   |
| `date_modification`     | DateTimeField  | Date de modification                               |

**Méthodes importantes:**
- `get_typed_value()`: Valeur convertie selon son type
- `get_setting(key, default)`: Récupérer un paramètre par clé

### 8.2. `AuditLog`
Modèle pour les logs d'audit.

| Champ                   | Type de Donnée | Description                                        |
|-------------------------|----------------|----------------------------------------------------|
| `utilisateur`           | ForeignKey     | Utilisateur (vers `User`)                         |
| `action`                | CharField      | Action (CREATE, UPDATE, DELETE, etc.)             |
| `description`           | TextField      | Description détaillée                              |
| `content_type`          | ForeignKey     | Type d'objet concerné                              |
| `object_id`             | PositiveIntegerField | ID de l'objet                                      |
| `objet_concerne`        | GenericForeignKey | Objet concerné                                     |
| `adresse_ip`            | GenericIPAddressField | Adresse IP                                         |
| `user_agent`            | TextField      | User Agent                                         |
| `donnees_avant`         | JSONField      | État avant modification                            |
| `donnees_apres`         | JSONField      | État après modification                            |
| `date_action`           | DateTimeField  | Date de l'action                                   |

### 8.3. `ContactMessage`
Modèle pour les messages de contact.

| Champ                   | Type de Donnée | Description                                        |
|-------------------------|----------------|----------------------------------------------------|
| `utilisateur`           | ForeignKey     | Utilisateur expéditeur (vers `User`)              |
| `nom`                   | CharField      | Nom de l'expéditeur                               |
| `email`                 | EmailField     | Email de l'expéditeur                              |
| `telephone`             | CharField      | Téléphone (optionnel)                             |
| `categorie`             | CharField      | Catégorie (SUPPORT, FACTURATION, etc.)            |
| `sujet`                 | CharField      | Sujet du message                                   |
| `message`               | TextField      | Contenu du message                                 |
| `statut`                | CharField      | Statut (NOUVEAU, EN_COURS, RESOLU, FERME)         |
| `assigne_a`             | ForeignKey     | Membre assigné (vers `User`)                      |
| `reponse`               | TextField      | Réponse de l'équipe                                |
| `date_creation`         | DateTimeField  | Date de réception                                  |
| `date_traitement`       | DateTimeField  | Date de prise en charge                            |
| `date_resolution`       | DateTimeField  | Date de résolution                                 |
| `adresse_ip`            | GenericIPAddressField | Adresse IP de l'expéditeur                         |

### 8.4. `FAQ`
Modèle pour les questions fréquemment posées.

| Champ                   | Type de Donnée | Description                                        |
|-------------------------|----------------|----------------------------------------------------|
| `question`              | CharField      | Question                                           |
| `reponse`               | TextField      | Réponse détaillée                                  |
| `categorie`             | CharField      | Catégorie de la FAQ                               |
| `ordre`                 | PositiveIntegerField | Ordre d'affichage                                  |
| `actif`                 | BooleanField   | FAQ active                                         |
| `nombre_vues`           | PositiveIntegerField | Nombre de consultations                            |
| `utile_oui`             | PositiveIntegerField | Votes "utile"                                      |
| `utile_non`             | PositiveIntegerField | Votes "pas utile"                                  |
| `date_creation`         | DateTimeField  | Date de création                                   |
| `date_modification`     | DateTimeField  | Date de modification                               |

### 8.5. `SystemStatus`
Modèle pour le statut du système.

| Champ                   | Type de Donnée | Description                                        |
|-------------------------|----------------|----------------------------------------------------|
| `service`               | CharField      | Nom du service                                     |
| `statut`                | CharField      | Statut (OPERATIONNEL, DEGRADE, PANNE)             |
| `description`           | TextField      | Description du statut                              |
| `temps_reponse`         | FloatField     | Temps de réponse en ms                             |
| `pourcentage_disponibilite`| FloatField     | Pourcentage de disponibilité                       |
| `derniere_verification` | DateTimeField  | Dernière vérification                              |
| `date_creation`         | DateTimeField  | Date de création                                   |

---

## Relations Importantes

### Relations Clés Entre Modèles

1. **User ↔ Event**: Un utilisateur peut créer plusieurs événements
2. **Event ↔ EventMedia**: Un événement peut avoir plusieurs médias
3. **User ↔ EventParticipation ↔ Event**: Relation many-to-many via EventParticipation
4. **User ↔ Subscription ↔ SubscriptionPlan**: Gestion des abonnements
5. **Payment ↔ Event/Subscription**: Paiements liés aux événements ou abonnements
6. **User ↔ Notification**: Notifications personnalisées par utilisateur

### Index de Base de Données

Les modèles incluent des index optimisés pour :
- Recherches par statut et date
- Filtres par utilisateur
- Requêtes de géolocalisation
- Statistiques et analytics

### Contraintes et Validations

- Validation des formats de téléphone béninois
- Contraintes d'unicité sur les champs critiques
- Validation des types de fichiers pour les uploads
- Limites de taille pour les champs JSON
- Validation des coordonnées géographiques

Cette documentation reflète l'état actuel et complet du système de données SpotVibe, incluant toutes les améliorations et nouvelles fonctionnalités ajoutées.

