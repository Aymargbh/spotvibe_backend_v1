# Documentation des Modèles de Données SpotVibe Backend

Ce document détaille la structure des modèles de données utilisés dans le backend de SpotVibe, y compris les champs, leurs types, et les relations entre les modèles. Cette documentation est essentielle pour le développement du frontend Flutter, permettant une compréhension claire des données manipulées par les APIs.

## 1. Application `authentication`

### 1.1. `SocialAccount`
Modèle pour les comptes de réseaux sociaux liés (Google, Facebook).

| Champ               | Type de Donnée | Description                                        |
|---------------------|----------------|----------------------------------------------------|
| `utilisateur`       | ForeignKey     | Utilisateur propriétaire du compte social (vers `User`) |
| `provider`          | CharField      | Fournisseur du compte social (choix: GOOGLE, FACEBOOK) |
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
| `statut`            | CharField      | Résultat de la tentative (choix: REUSSI, ECHEC, BLOQUE) |
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
| `statut`            | CharField      | Statut du token (choix: ACTIF, UTILISE, EXPIRE, ANNULE) |
| `date_creation`     | DateTimeField  | Date de création du token                          |
| `date_expiration`   | DateTimeField  | Date d'expiration du token                         |
| `date_utilisation`  | DateTimeField  | Date d'utilisation du token                        |
| `adresse_ip_creation`| GenericIPAddressField | IP utilisée pour créer le token                    |
| `adresse_ip_utilisation`| GenericIPAddressField | IP utilisée pour utiliser le token                 |

### 1.4. `EmailVerification`
Modèle pour la vérification des adresses email.

| Champ               | Type de Donnée | Description                                        |
|---------------------|----------------|----------------------------------------------------|
| `utilisateur`       | ForeignKey     | Utilisateur concerné (vers `User`)               |
| `email`             | EmailField     | Adresse email à vérifier                           |
| `code`              | CharField      | Code de vérification à 6 chiffres                  |
| `type_verification` | CharField      | Type de vérification (choix: INSCRIPTION, CHANGEMENT_EMAIL, REACTIVATION) |
| `statut`            | CharField      | Statut de la vérification (choix: EN_ATTENTE, VERIFIE, EXPIRE, ANNULE) |
| `date_creation`     | DateTimeField  | Date de création du code                           |
| `date_expiration`   | DateTimeField  | Date d'expiration du code                          |
| `date_verification` | DateTimeField  | Date de vérification réussie                       |
| `tentatives`        | PositiveIntegerField | Nombre de tentatives de vérification               |
| `max_tentatives`    | PositiveIntegerField | Nombre maximum de tentatives autorisées            |
| `adresse_ip`        | GenericIPAddressField | Adresse IP de création                             |

### 1.5. `TwoFactorAuth`
Modèle pour l'authentification à deux facteurs.

| Champ               | Type de Donnée | Description                                        |
|---------------------|----------------|----------------------------------------------------|
| `utilisateur`       | OneToOneField  | Utilisateur concerné (vers `User`)               |
| `actif`             | BooleanField   | Authentification 2FA activée                       |
| `methode`           | CharField      | Méthode d'authentification 2FA (choix: SMS, EMAIL, TOTP) |
| `secret_key`        | CharField      | Clé secrète pour TOTP                              |
| `codes_recuperation`| JSONField      | Codes de récupération d'urgence                    |
| `derniere_utilisation`| DateTimeField  | Dernière utilisation de 2FA                        |
| `date_activation`   | DateTimeField  | Date d'activation de 2FA                           |

## 2. Application `users`

### 2.1. `User`
Modèle utilisateur personnalisé pour SpotVibe, étendant `AbstractUser`.

| Champ                   | Type de Donnée | Description                                        |
|-------------------------|----------------|----------------------------------------------------|
| `telephone`             | CharField      | Numéro de téléphone au format béninois (+229XXXXXXXX) |
| `date_naissance`        | DateField      | Date de naissance de l'utilisateur                 |
| `photo_profil`          | ImageField     | Photo de profil de l'utilisateur (max 5MB)         |
| `bio`                   | TextField      | Description courte de l'utilisateur                |
| `est_verifie`           | BooleanField   | Indique si l'utilisateur a vérifié son identité    |
| `date_verification`     | DateTimeField  | Date à laquelle le compte a été vérifié            |
| `notifications_email`   | BooleanField   | Recevoir les notifications par email               |
| `notifications_push`    | BooleanField   | Recevoir les notifications push                    |
| `date_creation`         | DateTimeField  | Date de création du compte                         |
| `date_modification`     | DateTimeField  | Date de dernière modification du profil            |
| `derniere_connexion_ip` | GenericIPAddressField | Adresse IP de la dernière connexion                |

### 2.2. `UserVerification`
Modèle pour la vérification d'identité des utilisateurs.

| Champ                   | Type de Donnée | Description                                        |
|-------------------------|----------------|----------------------------------------------------|
| `utilisateur`           | OneToOneField  | Utilisateur concerné par la vérification (vers `User`) |
| `document_identite`     | FileField      | Carte d'identité, passeport ou autre document officiel |
| `document_selfie`       | ImageField     | Photo de l'utilisateur tenant son document d'identité |
| `statut`                | CharField      | Statut de la vérification (choix: EN_ATTENTE, APPROUVE, REJETE, EXPIRE) |
| `date_soumission`       | DateTimeField  | Date de soumission des documents                   |
| `date_validation`       | DateTimeField  | Date de validation par un administrateur           |
| `validateur`            | ForeignKey     | Administrateur qui a validé la vérification (vers `User`) |
| `commentaire_admin`     | TextField      | Commentaire de l'administrateur sur la vérification |

### 2.3. `Follow`
Modèle pour le système de suivi entre utilisateurs.

| Champ                   | Type de Donnée | Description                                        |
|-------------------------|----------------|----------------------------------------------------|
| `follower`              | ForeignKey     | Utilisateur qui suit (vers `User`)               |
| `following`             | ForeignKey     | Utilisateur suivi (vers `User`)                  |
| `date_suivi`            | DateTimeField  | Date à laquelle le suivi a commencé                |
| `notifications_activees`| BooleanField   | Recevoir des notifications pour les activités de cet utilisateur |

## 3. Application `core`

### 3.1. `AppSettings`
Modèle pour les paramètres de configuration de l'application.

| Champ               | Type de Donnée | Description                                        |
|---------------------|----------------|----------------------------------------------------|
| `cle`               | CharField      | Clé unique du paramètre                            |
| `valeur`            | TextField      | Valeur du paramètre                                |
| `type_valeur`       | CharField      | Type de données de la valeur (choix: STRING, INTEGER, FLOAT, BOOLEAN, JSON) |
| `description`       | TextField      | Description du paramètre                           |
| `categorie`         | CharField      | Catégorie du paramètre                             |
| `modifiable`        | BooleanField   | Paramètre modifiable via l'interface admin         |
| `date_creation`     | DateTimeField  | Date de création du paramètre                      |
| `date_modification` | DateTimeField  | Date de dernière modification                      |

### 3.2. `AuditLog`
Modèle pour les logs d'audit des actions importantes.

| Champ               | Type de Donnée | Description                                        |
|---------------------|----------------|----------------------------------------------------|
| `utilisateur`       | ForeignKey     | Utilisateur qui a effectué l'action (vers `User`) |
| `action`            | CharField      | Type d'action effectuée (choix: CREATE, UPDATE, DELETE, LOGIN, LOGOUT, APPROVE, REJECT, PAYMENT, REFUND, EXPORT, IMPORT, CONFIG) |
| `description`       | TextField      | Description détaillée de l'action                  |
| `content_type`      | ForeignKey     | Type d'objet concerné                              |
| `object_id`         | PositiveIntegerField | ID de l'objet concerné                             |
| `objet_concerne`    | GenericForeignKey | Objet concerné (relation générique)                |
| `adresse_ip`        | GenericIPAddressField | Adresse IP de l'utilisateur                        |
| `user_agent`        | TextField      | User Agent du navigateur                           |
| `donnees_avant`     | JSONField      | État de l'objet avant modification                 |
| `donnees_apres`     | JSONField      | État de l'objet après modification                 |
| `date_action`       | DateTimeField  | Date et heure de l'action                          |

### 3.3. `ContactMessage`
Modèle pour les messages de contact des utilisateurs.

| Champ               | Type de Donnée | Description                                        |
|---------------------|----------------|----------------------------------------------------|
| `utilisateur`       | ForeignKey     | Utilisateur expéditeur (si connecté) (vers `User`) |
| `nom`               | CharField      | Nom de l'expéditeur                                |
| `email`             | EmailField     | Email de l'expéditeur                              |
| `telephone`         | CharField      | Numéro de téléphone (optionnel)                    |
| `categorie`         | CharField      | Catégorie du message (choix: SUPPORT, FACTURATION, SUGGESTION, PLAINTE, AUTRE) |
| `sujet`             | CharField      | Sujet du message                                   |
| `message`           | TextField      | Contenu du message                                 |
| `statut`            | CharField      | Statut du message (choix: NOUVEAU, EN_COURS, RESOLU, FERME) |
| `assigne_a`         | ForeignKey     | Membre de l'équipe assigné (vers `User`)         |
| `reponse`           | TextField      | Réponse de l'équipe                                |
| `date_creation`     | DateTimeField  | Date de réception du message                       |
| `date_traitement`   | DateTimeField  | Date de première prise en charge                   |
| `date_resolution`   | DateTimeField  | Date de résolution du message                      |
| `adresse_ip`        | GenericIPAddressField | Adresse IP de l'expéditeur                         |

### 3.4. `FAQ`
Modèle pour les questions fréquemment posées.

| Champ               | Type de Donnée | Description                                        |
|---------------------|----------------|----------------------------------------------------|
| `question`          | CharField      | Question fréquemment posée                          |
| `reponse`           | TextField      | Réponse détaillée à la question                    |
| `categorie`         | CharField      | Catégorie de la question (choix: GENERAL, COMPTE, EVENEMENTS, PAIEMENTS, ABONNEMENTS, TECHNIQUE) |
| `ordre`             | PositiveIntegerField | Ordre d'affichage dans la liste                    |
| `actif`             | BooleanField   | Question visible publiquement                      |
| `nombre_vues`       | PositiveIntegerField | Nombre de fois que la question a été consultée     |
| `utile_oui`         | PositiveIntegerField | Nombre de votes 'utile'                            |
| `utile_non`         | PositiveIntegerField | Nombre de votes 'non utile'                        |
| `date_creation`     | DateTimeField  | Date de création de la FAQ                         |
| `date_modification` | DateTimeField  | Date de dernière modification                      |
| `createur`          | ForeignKey     | Utilisateur qui a créé cette FAQ (vers `User`)   |

### 3.5. `SystemStatus`
Modèle pour le statut du système et les maintenances.

| Champ               | Type de Donnée | Description                                        |
|---------------------|----------------|----------------------------------------------------|
| `titre`             | CharField      | Titre du statut ou incident                        |
| `description`       | TextField      | Description détaillée                              |
| `statut`            | CharField      | Statut actuel du système (choix: OPERATIONNEL, DEGRADED, MAINTENANCE, INCIDENT, HORS_LIGNE) |
| `severite`          | CharField      | Niveau de sévérité (choix: INFO, ATTENTION, CRITIQUE) |
| `date_debut`        | DateTimeField  | Date de début de l'incident/maintenance            |
| `date_fin_prevue`   | DateTimeField  | Date de fin prévue                                 |
| `date_fin_reelle`   | DateTimeField  | Date de fin réelle                                 |
| `afficher_banniere` | BooleanField   | Afficher une bannière d'information                |
| `bloquer_acces`     | BooleanField   | Bloquer l'accès à l'application                    |
| `date_creation`     | DateTimeField  | Date de création du statut                         |
| `date_modification` | DateTimeField  | Date de dernière modification                      |
| `createur`          | ForeignKey     | Utilisateur qui a créé ce statut (vers `User`)   |

## 4. Application `events`

### 4.1. `EventCategory`
Modèle pour les catégories d'événements.

| Champ               | Type de Donnée | Description                                        |
|---------------------|----------------|----------------------------------------------------|
| `nom`               | CharField      | Nom de la catégorie (ex: Mariage, Festival, Conférence) |
| `description`       | TextField      | Description de la catégorie                        |
| `icone`             | CharField      | Nom de l'icône (ex: fas fa-music)                  |
| `couleur`           | CharField      | Couleur hexadécimale (ex: #007bff)                 |
| `ordre`             | PositiveIntegerField | Ordre d'affichage dans les listes                  |
| `actif`             | BooleanField   | Catégorie active et visible                        |

### 4.2. `Event`
Modèle principal pour les événements.

| Champ                   | Type de Donnée | Description                                        |
|-------------------------|----------------|----------------------------------------------------|
| `titre`                 | CharField      | Titre de l'événement                               |
| `description`           | TextField      | Description détaillée de l'événement               |
| `description_courte`    | CharField      | Résumé court pour les listes                       |
| `date_debut`            | DateTimeField  | Date et heure de début de l'événement              |
| `date_fin`              | DateTimeField  | Date et heure de fin de l'événement                |
| `lieu`                  | CharField      | Nom du lieu de l'événement                         |
| `adresse`               | TextField      | Adresse complète du lieu                           |
| `latitude`              | DecimalField   | Coordonnée latitude pour la carte                  |
| `longitude`             | DecimalField   | Coordonnée longitude pour la carte                 |
| `lien_google_maps`      | URLField       | Lien vers Google Maps pour le lieu                 |
| `createur`              | ForeignKey     | Utilisateur qui a créé l'événement (vers `User`) |
| `categorie`             | ForeignKey     | Catégorie de l'événement (vers `EventCategory`)  |
| `type_acces`            | CharField      | Type d'accès à l'événement (choix: GRATUIT, PAYANT, INVITATION) |
| `prix`                  | DecimalField   | Prix d'entrée en FCFA                              |
| `capacite_max`          | PositiveIntegerField | Nombre maximum de participants (optionnel)         |
| `image_couverture`      | ImageField     | Image principale de l'événement                    |
| `statut`                | CharField      | Statut de l'événement (choix: BROUILLON, EN_ATTENTE, VALIDE, REJETE, ANNULE, TERMINE) |
| `date_validation`       | DateTimeField  | Date de validation par un administrateur           |
| `validateur`            | ForeignKey     | Administrateur qui a validé l'événement (vers `User`) |
| `commentaire_validation`| TextField      | Commentaire de l'administrateur                    |
| `nombre_vues`           | PositiveIntegerField | Nombre de fois que l'événement a été consulté      |
| `nombre_partages`       | PositiveIntegerField | Nombre de fois que l'événement a été partagé       |
| `date_creation`         | DateTimeField  | Date de création de l'événement                    |
| `date_modification`     | DateTimeField  | Date de dernière modification                      |
| `billetterie_activee`   | BooleanField   | Utiliser le système de billetterie intégré         |
| `commission_billetterie`| DecimalField   | Commission en pourcentage sur les ventes           |

### 4.3. `EventParticipation`
Modèle pour la participation aux événements.

| Champ               | Type de Donnée | Description                                        |
|---------------------|----------------|----------------------------------------------------|
| `utilisateur`       | ForeignKey     | Utilisateur participant (vers `User`)            |
| `evenement`         | ForeignKey     | Événement concerné (vers `Event`)                |
| `statut`            | CharField      | Type de participation (choix: INTERESSE, PARTICIPE, A_PARTICIPE, ANNULE) |
| `date_participation`| DateTimeField  | Date d'inscription à l'événement                   |
| `date_modification` | DateTimeField  | Date de dernière modification du statut            |
| `commentaire`       | TextField      | Commentaire du participant                         |

### 4.4. `EventShare`
Modèle pour le partage d'événements sur les réseaux sociaux.

| Champ               | Type de Donnée | Description                                        |
|---------------------|----------------|----------------------------------------------------|
| `utilisateur`       | ForeignKey     | Utilisateur qui partage (vers `User`)            |
| `evenement`         | ForeignKey     | Événement partagé (vers `Event`)                 |
| `plateforme`        | CharField      | Plateforme de partage (choix: FACEBOOK, TWITTER, INSTAGRAM, WHATSAPP, LINKEDIN, EMAIL, LIEN) |
| `date_partage`      | DateTimeField  | Date du partage                                    |
| `lien_genere`       | URLField       | Lien personnalisé généré pour le partage         |
| `nombre_clics`      | PositiveIntegerField | Nombre de clics sur le lien partagé                |

### 4.5. `EventTicket`
Modèle pour la billetterie des événements.

| Champ               | Type de Donnée | Description                                        |
|---------------------|----------------|----------------------------------------------------|
| `uuid`              | UUIDField      | Identifiant unique du billet                       |
| `evenement`         | ForeignKey     | Événement concerné (vers `Event`)                |
| `utilisateur`       | ForeignKey     | Acheteur du billet (vers `User`)                 |
| `prix`              | DecimalField   | Prix payé pour le billet                           |
| `quantite`          | PositiveIntegerField | Nombre de billets                                  |
| `statut`            | CharField      | Statut du billet (choix: EN_ATTENTE, PAYE, ANNULE, REMBOURSE, UTILISE) |
| `code_qr`           | ImageField     | Code QR du billet                                  |
| `date_achat`        | DateTimeField  | Date d'achat du billet                             |
| `date_utilisation`  | DateTimeField  | Date d'utilisation du billet                       |
| `valide_par`        | ForeignKey     | Utilisateur qui a validé le billet (vers `User`) |
| `notes_validation`  | TextField      | Notes de validation                                |

## 5. Application `subscriptions`

### 5.1. `SubscriptionPlan`
Modèle pour les plans d'abonnement.

| Champ               | Type de Donnée | Description                                        |
|---------------------|----------------|----------------------------------------------------|
| `nom`               | CharField      | Nom du plan d'abonnement                           |
| `type_plan`         | CharField      | Type de plan d'abonnement (choix: STANDARD, PREMIUM, GOLD) |
| `prix`              | DecimalField   | Prix de l'abonnement en FCFA                       |
| `duree`             | CharField      | Durée de l'abonnement (choix: MENSUEL, TRIMESTRIEL, ANNUEL) |
| `description`       | TextField      | Description du plan d'abonnement                   |
| `max_evenements_par_mois`| PositiveIntegerField | Nombre maximum d'événements par mois (null = illimité) |
| `commission_reduite`| DecimalField   | Taux de commission réduit en pourcentage           |
| `support_prioritaire`| BooleanField   | Accès au support prioritaire                       |
| `analytics_avances` | BooleanField   | Accès aux statistiques avancées                    |
| `promotion_evenements`| BooleanField   | Mise en avant automatique des événements           |
| `personnalisation_profil`| BooleanField   | Options de personnalisation avancées du profil     |
| `actif`             | BooleanField   | Plan disponible à la souscription                  |
| `ordre`             | PositiveIntegerField | Ordre d'affichage dans les listes                  |
| `date_creation`     | DateTimeField  | Date de création du plan                           |
| `date_modification` | DateTimeField  | Date de dernière modification                      |

### 5.2. `Subscription`
Modèle pour les abonnements des utilisateurs.

| Champ               | Type de Donnée | Description                                        |
|---------------------|----------------|----------------------------------------------------|
| `utilisateur`       | ForeignKey     | Utilisateur abonné (vers `User`)                 |
| `plan`              | ForeignKey     | Plan d'abonnement souscrit (vers `SubscriptionPlan`) |
| `date_debut`        | DateTimeField  | Date de début de l'abonnement                      |
| `date_fin`          | DateTimeField  | Date de fin de l'abonnement                        |
| `statut`            | CharField      | Statut de l'abonnement (choix: ACTIF, EXPIRE, ANNULE, SUSPENDU, EN_ATTENTE) |
| `prix_paye`         | DecimalField   | Prix effectivement payé pour cet abonnement       |
| `renouvellement_automatique`| BooleanField   | Renouveler automatiquement l'abonnement            |
| `date_creation`     | DateTimeField  | Date de souscription                               |
| `date_modification` | DateTimeField  | Date de dernière modification                      |
| `reference_paiement`| CharField      | Référence du paiement Mobile Money                 |
| `evenements_crees_ce_mois`| PositiveIntegerField | Nombre d'événements créés ce mois                  |
| `derniere_reinitialisation_compteur`| DateTimeField  | Dernière réinitialisation du compteur mensuel      |

### 5.3. `SubscriptionFeature`
Modèle pour les fonctionnalités des plans d'abonnement.

| Champ               | Type de Donnée | Description                                        |
|---------------------|----------------|----------------------------------------------------|
| `plan`              | ForeignKey     | Plan d'abonnement (vers `SubscriptionPlan`)      |
| `nom`               | CharField      | Nom de la fonctionnalité                           |
| `description`       | TextField      | Description détaillée de la fonctionnalité         |
| `inclus`            | BooleanField   | Fonctionnalité incluse dans ce plan                |
| `limite`            | CharField      | Limite de la fonctionnalité (ex: '10 par mois', 'Illimité') |
| `ordre`             | PositiveIntegerField | Ordre d'affichage dans les listes                  |

### 5.4. `SubscriptionHistory`
Modèle pour l'historique des abonnements.

| Champ               | Type de Donnée | Description                                        |
|---------------------|----------------|----------------------------------------------------|
| `subscription`      | ForeignKey     | Abonnement concerné (vers `Subscription`)        |
| `action`            | CharField      | Type d'action effectuée (choix: SOUSCRIPTION, RENOUVELLEMENT, CHANGEMENT_PLAN, ANNULATION, SUSPENSION, REACTIVATION) |
| `ancien_statut`     | CharField      | Statut avant l'action                              |
| `nouveau_statut`    | CharField      | Statut après l'action                              |
| `commentaire`       | TextField      | Commentaire sur l'action                           |
| `date_action`       | DateTimeField  | Date de l'action                                   |
| `utilisateur_action`| ForeignKey     | Utilisateur qui a effectué l'action (admin) (vers `User`) |

## 6. Application `payments`

### 6.1. `Payment`
Modèle principal pour tous les paiements sur la plateforme.

| Champ               | Type de Donnée | Description                                        |
|---------------------|----------------|----------------------------------------------------|
| `uuid`              | UUIDField      | Identifiant unique du paiement                     |
| `utilisateur`       | ForeignKey     | Utilisateur qui effectue le paiement (vers `User`) |
| `type_paiement`     | CharField      | Type de paiement effectué (choix: ABONNEMENT, BILLET, COMMISSION, REMBOURSEMENT) |
| `montant`           | DecimalField   | Montant du paiement en FCFA                        |
| `frais`             | DecimalField   | Frais de transaction en FCFA                       |
| `montant_net`       | DecimalField   | Montant net reçu (montant - frais)                 |
| `statut`            | CharField      | Statut du paiement (choix: EN_ATTENTE, EN_COURS, REUSSI, ECHEC, ANNULE, REMBOURSE) |
| `methode_paiement`  | CharField      | Méthode de paiement utilisée (choix: MOMO_MTN, MOMO_MOOV, CARTE_BANCAIRE, VIREMENT, ESPECES) |
| `reference_externe` | CharField      | Référence du prestataire de paiement               |
| `reference_interne` | CharField      | Référence interne SpotVibe                         |
| `subscription`      | ForeignKey     | Abonnement concerné (si applicable) (vers `Subscription`) |
| `event_ticket`      | ForeignKey     | Billet concerné (si applicable) (vers `EventTicket`) |
| `description`       | TextField      | Description du paiement                            |
| `date_creation`     | DateTimeField  | Date de création du paiement                       |
| `date_traitement`   | DateTimeField  | Date de traitement du paiement                     |
| `date_expiration`   | DateTimeField  | Date d'expiration du paiement                      |
| `telephone_paiement`| CharField      | Numéro de téléphone utilisé pour le paiement       |
| `donnees_reponse`   | JSONField      | Données de réponse du prestataire de paiement      |

### 6.2. `MomoTransaction`
Modèle spécifique pour les transactions Mobile Money.

| Champ               | Type de Donnée | Description                                        |
|---------------------|----------------|----------------------------------------------------|
| `payment`           | OneToOneField  | Paiement associé (vers `Payment`)                |
| `operateur`         | CharField      | Opérateur Mobile Money (choix: MTN, MOOV)          |
| `numero_telephone`  | CharField      | Numéro de téléphone Mobile Money                   |
| `type_transaction`  | CharField      | Type de transaction Mobile Money (choix: PAYMENT, REFUND, TRANSFER) |
| `transaction_id`    | CharField      | Identifiant unique de la transaction chez l'opérateur |
| `reference_operateur`| CharField      | Référence fournie par l'opérateur                  |
| `code_reponse`      | CharField      | Code de réponse de l'opérateur                     |
| `message_reponse`   | TextField      | Message de réponse de l'opérateur                  |
| `date_initiation`   | DateTimeField  | Date d'initiation de la transaction                |
| `date_confirmation` | DateTimeField  | Date de confirmation par l'opérateur               |
| `webhook_recu`      | BooleanField   | Webhook de confirmation reçu                       |
| `donnees_webhook`   | JSONField      | Données reçues via webhook                         |

### 6.3. `Commission`
Modèle pour les commissions perçues par la plateforme.

| Champ               | Type de Donnée | Description                                        |
|---------------------|----------------|----------------------------------------------------|
| `payment`           | ForeignKey     | Paiement générateur de commission (vers `Payment`) |
| `type_commission`   | CharField      | Type de commission (choix: BILLETTERIE, ABONNEMENT, SERVICE) |
| `montant_base`      | DecimalField   | Montant sur lequel la commission est calculée      |
| `taux_commission`   | DecimalField   | Taux de commission en pourcentage                  |
| `montant_commission`| DecimalField   | Montant de commission calculé                      |
| `statut`            | CharField      | Statut de la commission (choix: EN_ATTENTE, CALCULEE, PAYEE, ANNULEE) |
| `event`             | ForeignKey     | Événement concerné (si applicable) (vers `Event`) |
| `organisateur`      | ForeignKey     | Organisateur qui doit la commission (vers `User`) |
| `date_calcul`       | DateTimeField  | Date de calcul de la commission                    |
| `date_paiement`     | DateTimeField  | Date de paiement de la commission                  |
| `notes`             | TextField      | Notes sur la commission                            |

### 6.4. `Refund`
Modèle pour les remboursements.

| Champ               | Type de Donnée | Description                                        |
|---------------------|----------------|----------------------------------------------------|
| `payment_original`  | ForeignKey     | Paiement à rembourser (vers `Payment`)           |
| `demandeur`         | ForeignKey     | Utilisateur qui demande le remboursement (vers `User`) |
| `montant_remboursement`| DecimalField   | Montant à rembourser                               |
| `raison`            | CharField      | Raison du remboursement (choix: ANNULATION_EVENT, DEMANDE_CLIENT, ERREUR_PAIEMENT, FRAUDE, AUTRE) |
| `description`       | TextField      | Description détaillée de la demande                |
| `statut`            | CharField      | Statut du remboursement (choix: DEMANDE, EN_COURS, APPROUVE, REJETE, REMBOURSE) |
| `date_demande`      | DateTimeField  | Date de la demande de remboursement                |
| `date_traitement`   | DateTimeField  | Date de traitement de la demande                   |
| `date_remboursement`| DateTimeField  | Date effective du remboursement                    |
| `traiteur`          | ForeignKey     | Administrateur qui a traité la demande (vers `User`) |
| `commentaire_admin` | TextField      | Commentaire de l'administrateur                    |





## 7. Application `notifications`

### 7.1. `NotificationTemplate`
Modèle pour les templates de notifications.

| Champ               | Type de Donnée | Description                                        |
|---------------------|----------------|----------------------------------------------------|
| `type_notification` | CharField      | Type de notification (choix: EVENT_CREATED, EVENT_APPROVED, EVENT_REJECTED, EVENT_REMINDER, EVENT_CANCELLED, NEW_FOLLOWER, FOLLOW_EVENT, PAYMENT_SUCCESS, PAYMENT_FAILED, SUBSCRIPTION_EXPIRING, SUBSCRIPTION_EXPIRED, TICKET_PURCHASED, VERIFICATION_APPROVED, VERIFICATION_REJECTED, SYSTEM_MAINTENANCE, WELCOME) |
| `nom`               | CharField      | Nom du template                                    |
| `description`       | TextField      | Description du template                            |
| `titre_email`       | CharField      | Titre pour les notifications email                 |
| `contenu_email`     | TextField      | Contenu HTML pour les emails                       |
| `titre_push`        | CharField      | Titre pour les notifications push                  |
| `contenu_push`      | CharField      | Contenu pour les notifications push                |
| `contenu_sms`       | CharField      | Contenu pour les SMS (max 160 caractères)          |
| `contenu_in_app`    | TextField      | Contenu pour les notifications dans l'application  |
| `canaux_actifs`     | JSONField      | Liste des canaux activés pour ce template          |
| `variables_disponibles`| JSONField      | Variables disponibles pour ce template (ex: {user_name}, {event_title}) |
| `actif`             | BooleanField   | Template actif                                     |
| `date_creation`     | DateTimeField  | Date de création du template                       |
| `date_modification` | DateTimeField  | Date de dernière modification                      |

### 7.2. `Notification`
Modèle pour les notifications individuelles.

| Champ               | Type de Donnée | Description                                        |
|---------------------|----------------|----------------------------------------------------|
| `utilisateur`       | ForeignKey     | Destinataire de la notification (vers `User`)    |
| `type_notification` | CharField      | Type de notification                               |
| `titre`             | CharField      | Titre de la notification                           |
| `message`           | TextField      | Contenu de la notification                         |
| `content_type`      | ForeignKey     | Type d'objet concerné                              |
| `object_id`         | PositiveIntegerField | ID de l'objet concerné                             |
| `objet_concerne`    | GenericForeignKey | Objet concerné (relation générique)                |
| `priorite`          | CharField      | Priorité de la notification (choix: BASSE, NORMALE, HAUTE, URGENTE) |
| `statut`            | CharField      | Statut de la notification (choix: EN_ATTENTE, ENVOYE, LIVRE, LU, ECHEC) |
| `date_creation`     | DateTimeField  | Date de création de la notification                |
| `date_envoi`        | DateTimeField  | Date d'envoi de la notification                    |
| `date_lecture`      | DateTimeField  | Date de lecture par l'utilisateur                  |
| `date_expiration`   | DateTimeField  | Date d'expiration de la notification               |
| `lien_action`       | URLField       | Lien vers une action spécifique                    |
| `donnees_supplementaires`| JSONField      | Données supplémentaires pour l'application         |

### 7.3. `NotificationPreference`
Modèle pour les préférences de notification des utilisateurs.

| Champ               | Type de Donnée | Description                                        |
|---------------------|----------------|----------------------------------------------------|
| `utilisateur`       | ForeignKey     | Utilisateur concerné (vers `User`)               |
| `type_notification` | CharField      | Type de notification                               |
| `canal`             | CharField      | Canal de notification (choix: EMAIL, PUSH, SMS, IN_APP) |
| `actif`             | BooleanField   | Recevoir ce type de notification sur ce canal      |
| `frequence`         | CharField      | Fréquence de notification (choix: IMMEDIATE, QUOTIDIEN, HEBDOMADAIRE, JAMAIS) |
| `heure_envoi`       | TimeField      | Heure préférée pour les notifications groupées     |
| `date_creation`     | DateTimeField  | Date de création de la préférence                  |
| `date_modification` | DateTimeField  | Date de dernière modification                      |

### 7.4. `PushToken`
Modèle pour les tokens de notification push.

| Champ               | Type de Donnée | Description                                        |
|---------------------|----------------|----------------------------------------------------|
| `utilisateur`       | ForeignKey     | Utilisateur propriétaire du token (vers `User`)  |
| `token`             | TextField      | Token de notification push                         |
| `plateforme`        | CharField      | Plateforme de l'appareil (choix: ANDROID, IOS, WEB) |
| `nom_appareil`      | CharField      | Nom de l'appareil                                  |
| `version_app`       | CharField      | Version de l'application                           |
| `version_os`        | CharField      | Version du système d'exploitation                  |
| `actif`             | BooleanField   | Token actif pour l'envoi de notifications          |
| `derniere_utilisation`| DateTimeField  | Dernière fois que le token a été utilisé           |
| `date_creation`     | DateTimeField  | Date d'enregistrement du token                     |
| `notifications_envoyees`| PositiveIntegerField | Nombre de notifications envoyées à ce token        |
| `notifications_livrees`| PositiveIntegerField | Nombre de notifications livrées avec succès        |




### 7.5. `NotificationBatch`
Modèle pour les envois groupés de notifications.

| Champ               | Type de Donnée | Description                                        |
|---------------------|----------------|----------------------------------------------------|
| `nom`               | CharField      | Nom de la campagne                                 |
| `description`       | TextField      | Description de la campagne                         |
| `template`          | ForeignKey     | Template utilisé pour cette campagne (vers `NotificationTemplate`) |
| `destinataires`     | ManyToManyField| Utilisateurs ciblés par cette campagne (vers `User`) |
| `criteres_ciblage`  | JSONField      | Critères de sélection des destinataires            |
| `date_planifiee`    | DateTimeField  | Date et heure d'envoi planifiée                    |
| `statut`            | CharField      | Statut de la campagne (choix: PLANIFIE, EN_COURS, TERMINE, ECHEC, ANNULE) |
| `nombre_destinataires`| PositiveIntegerField | Nombre total de destinataires                      |
| `nombre_envoyes`    | PositiveIntegerField | Nombre de notifications envoyées                   |
| `nombre_livres`     | PositiveIntegerField | Nombre de notifications livrées                    |
| `nombre_lus`        | PositiveIntegerField | Nombre de notifications lues                       |
| `date_creation`     | DateTimeField  | Date de création de la campagne                    |
| `date_debut_envoi`  | DateTimeField  | Date de début d'envoi effectif                     |
| `date_fin_envoi`    | DateTimeField  | Date de fin d'envoi                                |
| `createur`          | ForeignKey     | Utilisateur qui a créé cette campagne (vers `User`) |


