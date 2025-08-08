"""
Modèles pour la gestion des événements dans SpotVibe.

Ce module définit tous les modèles liés aux événements :
- EventCategory : Catégories d'événements
- Event : Événements principaux
- EventParticipation : Participation aux événements
- EventShare : Partages d'événements
- EventTicket : Billetterie
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from PIL import Image
import qrcode
from io import BytesIO
from django.core.files import File
import uuid
import subprocess
from PIL import Image
from django.core.files.base import ContentFile
import ffmpeg
import tempfile
from datetime import timedelta
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator, FileExtensionValidator
import os
from apps.users.models import Entity


User = get_user_model()


class EventCategory(models.Model):
    """
    Modèle pour les catégories d'événements.
    
    Permet de classer les événements par type (mariage, festival, etc.)
    avec des icônes et couleurs personnalisées.
    """
    
    nom = models.CharField(
        _('Nom'),
        max_length=100,
        unique=True,
        help_text="Nom de la catégorie (ex: Mariage, Festival, Conférence)"
    )
    
    description = models.TextField(
        _('Description'),
        blank=True,
        help_text="Description de la catégorie"
    )
    
    icone = models.CharField(
        _('Icône'),
        max_length=50,
        blank=True,
        help_text="Nom de l'icône (ex: fas fa-music)"
    )
    
    couleur = models.CharField(
        _('Couleur'),
        max_length=7,
        default='#007bff',
        help_text="Couleur hexadécimale (ex: #007bff)"
    )
    
    ordre = models.PositiveIntegerField(
        _('Ordre d\'affichage'),
        default=0,
        help_text="Ordre d'affichage dans les listes"
    )
    
    actif = models.BooleanField(
        _('Actif'),
        default=True,
        help_text="Catégorie active et visible"
    )
    
    class Meta:
        verbose_name = _('Catégorie d\'événement')
        verbose_name_plural = _('Catégories d\'événement')
        ordering = ['ordre', 'nom']
    
    def __str__(self):
        """Représentation string de la catégorie."""
        return self.nom
    
    def get_events_count(self):
        """Retourne le nombre d'événements dans cette catégorie."""
        return self.events.filter(statut='VALIDE').count()


class EventMedia(models.Model):
    """
    Modèle pour gérer les médias (images et vidéos) des événements.
    Permet d'avoir une galerie complète pour chaque événement.
    """
    
    TYPE_CHOICES = [
        ('image', _('Image')),
        ('video', _('Vidéo')),
    ]
    
    USAGE_CHOICES = [
        ('galerie', _('Galerie')),
        ('couverture', _('Image de couverture')),
        ('post_cover', _('Couverture de post')),
        ('thumbnail', _('Miniature')),
    ]
    
    # Relations
    evenement = models.ForeignKey(
        'Event',
        on_delete=models.CASCADE,
        related_name='medias',
        verbose_name=_('Événement')
    )
    
    # Type de média
    type_media = models.CharField(
        _('Type de média'),
        max_length=10,
        choices=TYPE_CHOICES,
        help_text="Type du fichier média"
    )
    
    usage = models.CharField(
        _('Usage'),
        max_length=20,
        choices=USAGE_CHOICES,
        default='galerie',
        help_text="Usage prévu pour ce média"
    )
    
    # Fichiers
    fichier = models.FileField(
        _('Fichier'),
        upload_to='events/medias/',
        validators=[
            FileExtensionValidator(
                allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'mp4', 'avi', 'mov', 'webm']
            )
        ],
        help_text="Fichier image ou vidéo"
    )
    
    # Miniature pour les vidéos
    thumbnail = models.ImageField(
        _('Miniature'),
        upload_to='events/thumbnails/',
        null=True,
        blank=True,
        help_text="Miniature générée automatiquement pour les vidéos"
    )
    
    # Métadonnées
    titre = models.CharField(
        _('Titre'),
        max_length=200,
        blank=True,
        help_text="Titre ou description du média"
    )
    
    description = models.TextField(
        _('Description'),
        blank=True,
        help_text="Description détaillée du média"
    )
    
    # Ordre d'affichage
    ordre = models.PositiveIntegerField(
        _('Ordre'),
        default=0,
        help_text="Ordre d'affichage dans la galerie"
    )
    
    # Propriétés techniques
    taille_fichier = models.PositiveIntegerField(
        _('Taille du fichier'),
        null=True,
        blank=True,
        help_text="Taille du fichier en octets"
    )
    
    largeur = models.PositiveIntegerField(
        _('Largeur'),
        null=True,
        blank=True,
        help_text="Largeur en pixels (pour les images)"
    )
    
    hauteur = models.PositiveIntegerField(
        _('Hauteur'),
        null=True,
        blank=True,
        help_text="Hauteur en pixels (pour les images)"
    )
    
    duree = models.DurationField(
        _('Durée'),
        null=True,
        blank=True,
        help_text="Durée de la vidéo"
    )
    
    # Statut
    est_active = models.BooleanField(
        _('Actif'),
        default=True,
        help_text="Média visible dans la galerie"
    )
    
    # Métadonnées système
    date_upload = models.DateTimeField(
        _('Date d\'upload'),
        auto_now_add=True,
        help_text="Date d'ajout du média"
    )
    
    uploade_par = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='medias_uploaded',
        verbose_name=_('Uploadé par'),
        help_text="Utilisateur qui a uploadé ce média"
    )
    
    class Meta:
        verbose_name = _('Média d\'événement')
        verbose_name_plural = _('Médias d\'événement')
        ordering = ['ordre', 'date_upload']
        unique_together = ['evenement', 'usage', 'ordre']
    
    def __str__(self):
        return f"{self.evenement.titre} - {self.get_type_media_display()} #{self.ordre}"
    
    def save(self, *args, **kwargs):
        """Sauvegarde personnalisée pour traiter les médias."""
        
        # Déterminer le type de fichier automatiquement
        if self.fichier:
            ext = os.path.splitext(self.fichier.name)[1].lower()
            if ext in ['.jpg', '.jpeg', '.png', '.gif']:
                self.type_media = 'image'
            elif ext in ['.mp4', '.avi', '.mov', '.webm']:
                self.type_media = 'video'
            
            # Enregistrer la taille du fichier
            self.taille_fichier = self.fichier.size
        
        super().save(*args, **kwargs)
        
        # Post-traitement après sauvegarde
        if self.fichier:
            self._process_media()
    
    def _process_media(self):
        """Traite le média après upload (redimensionnement, génération de miniatures, etc.)"""
        
        if self.type_media == 'image':
            self._process_image()
        elif self.type_media == 'video':
            self._process_video()
    
    def _process_image(self):
        """Traite les images : redimensionnement et extraction des dimensions."""
        try:
            with Image.open(self.fichier.path) as img:
                # Enregistrer les dimensions originales
                self.largeur, self.hauteur = img.size
                
                # Redimensionner selon l'usage
                if self.usage == 'couverture':
                    max_size = (1200, 800)
                elif self.usage == 'post_cover':
                    max_size = (800, 600)
                elif self.usage == 'thumbnail':
                    max_size = (300, 300)
                else:  # galerie
                    max_size = (1000, 1000)
                
                # Redimensionner si nécessaire
                if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                    img.thumbnail(max_size, Image.Resampling.LANCZOS)
                    img.save(self.fichier.path, optimize=True, quality=85)
                    
                    # Mettre à jour les dimensions
                    self.largeur, self.hauteur = img.size
                
                # Sauvegarder les modifications
                EventMedia.objects.filter(id=self.id).update(
                    largeur=self.largeur,
                    hauteur=self.hauteur
                )
                
        except Exception as e:
            print(f"Erreur lors du traitement de l'image {self.id}: {e}")
    
    def _process_video(self):
        """Traite les vidéos : génération de miniatures et extraction des métadonnées."""
        try:
            video_path = self.fichier.path
            
            # 1. Extraire les métadonnées de la vidéo
            probe = ffmpeg.probe(video_path)
            video_info = next(
                stream for stream in probe['streams'] if stream['codec_type'] == 'video'
            )
            
            # Enregistrer les dimensions
            self.largeur = int(video_info['width'])
            self.hauteur = int(video_info['height'])
            
            # Enregistrer la durée (convertie en timedelta)
            duration = float(probe['format']['duration'])
            self.duree = timedelta(seconds=duration)
            
            # 2. Générer une miniature (thumbnail)
            thumbnail_path = self._generate_video_thumbnail(video_path)
            
            if thumbnail_path and os.path.exists(thumbnail_path):
                with open(thumbnail_path, 'rb') as thumb_file:
                    thumb_content = ContentFile(thumb_file.read())
                    thumb_name = os.path.basename(thumbnail_path)
                    
                    # Sauvegarder la miniature
                    if self.thumbnail:
                        self.thumbnail.delete(save=False)
                    
                    self.thumbnail.save(
                        f"thumb_{os.path.splitext(self.fichier.name)[0]}.jpg",
                        thumb_content,
                        save=False
                    )
                
                # Supprimer le fichier temporaire
                os.remove(thumbnail_path)
            
            # 3. Optimiser la vidéo si nécessaire (transcodage)
            if not video_info['codec_name'] in ['h264', 'vp9']:
                self._optimize_video(video_path)
            
            # Sauvegarder les métadonnées
            EventMedia.objects.filter(id=self.id).update(
                largeur=self.largeur,
                hauteur=self.hauteur,
                duree=self.duree
            )
            
        except Exception as e:
            print(f"Erreur lors du traitement de la vidéo {self.id}: {e}")
            # Vous pourriez logger cette erreur dans un système de logging

    def _generate_video_thumbnail(self, video_path):
        """
        Génère une miniature à partir de la vidéo.
        Retourne le chemin du fichier temporaire de la miniature.
        """
        try:
            # Créer un fichier temporaire pour la miniature
            temp_dir = tempfile.gettempdir()
            thumb_name = f"thumb_{os.path.basename(video_path)}.jpg"
            thumb_path = os.path.join(temp_dir, thumb_name)
            
            # Extraire une frame au milieu de la vidéo
            (
                ffmpeg.input(video_path)
                .filter('select', 'gte(n,1)')  # Première frame
                .output(thumb_path, vframes=1, format='image2', vcodec='mjpeg')
                .overwrite_output()
                .run(quiet=True)
            )
            
            # Redimensionner la miniature si nécessaire
            with Image.open(thumb_path) as img:
                max_size = (800, 450)  # Format 16:9
                if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                    img.thumbnail(max_size, Image.Resampling.LANCZOS)
                    img.save(thumb_path, quality=85)
            
            return thumb_path
        
        except Exception as e:
            print(f"Erreur génération thumbnail: {e}")
            return None

    def _optimize_video(self, video_path):
        """
        Optimise la vidéo pour le web (transcodage en H.264).
        Crée une copie optimisée et remplace le fichier original.
        """
        try:
            # Créer un fichier temporaire pour la version optimisée
            temp_dir = tempfile.gettempdir()
            optimized_name = f"optimized_{os.path.basename(video_path)}"
            optimized_path = os.path.join(temp_dir, optimized_name)
            
            # Paramètres d'optimisation
            (
                ffmpeg.input(video_path)
                .output(
                    optimized_path,
                    vcodec='libx264',
                    crf=23,  # Qualité (18-28, plus bas = meilleure qualité)
                    preset='fast',
                    acodec='aac',
                    movflags='faststart',  # Pour le streaming
                    pix_fmt='yuv420p'  # Compatibilité maximale
                )
                .overwrite_output()
                .run(quiet=True)
            )
            
            # Remplacer le fichier original par la version optimisée
            if os.path.exists(optimized_path):
                # Supprimer l'ancien fichier
                if os.path.exists(video_path):
                    os.remove(video_path)
                
                # Déplacer le nouveau fichier
                os.rename(optimized_path, video_path)
                
                # Mettre à jour la taille du fichier
                self.taille_fichier = os.path.getsize(video_path)
                EventMedia.objects.filter(id=self.id).update(
                    taille_fichier=self.taille_fichier
                )
        
        except Exception as e:
            print(f"Erreur optimisation vidéo: {e}")
            # Si l'optimisation échoue, on garde la vidéo originale
    
    def get_file_size_display(self):
        """Retourne la taille du fichier dans un format lisible."""
        if not self.taille_fichier:
            return "Inconnue"
        
        size = self.taille_fichier
        for unit in ['o', 'Ko', 'Mo', 'Go']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} To"
    
    def is_image(self):
        """Vérifie si le média est une image."""
        return self.type_media == 'image'
    
    def is_video(self):
        """Vérifie si le média est une vidéo."""
        return self.type_media == 'video'
    
    def get_display_url(self):
        """Retourne l'URL d'affichage (fichier ou miniature pour les vidéos)."""
        if self.is_video() and self.thumbnail:
            return self.thumbnail.url
        return self.fichier.url


# Modification du modèle Event existant
class Event(models.Model):
    """
    Modèle principal pour les événements - VERSION MISE À JOUR
    
    Modifications apportées :
    - Suppression de image_couverture (remplacé par le système de médias)
    - Ajout de méthodes pour gérer les médias
    """
    
    STATUT_CHOICES = [
        ('BROUILLON', _('Brouillon')),
        ('EN_ATTENTE', _('En attente de validation')),
        ('VALIDE', _('Validé')),
        ('REJETE', _('Rejeté')),
        ('ANNULE', _('Annulé')),
        ('TERMINE', _('Terminé')),
    ]
    
    TYPE_ACCES_CHOICES = [
        ('GRATUIT', _('Gratuit')),
        ('PAYANT', _('Payant')),
        ('INVITATION', _('Sur invitation')),
    ]
    
    # Informations de base
    titre = models.CharField(
        _('Titre'),
        max_length=200,
        help_text="Titre de l'événement"
    )
    
    description = models.TextField(
        _('Description'),
        help_text="Description détaillée de l'événement"
    )
    
    description_courte = models.CharField(
        _('Description courte'),
        max_length=300,
        blank=True,
        help_text="Résumé court pour les listes"
    )
    
    # Dates et horaires
    date_debut = models.DateTimeField(
        _('Date de début'),
        help_text="Date et heure de début de l'événement"
    )
    
    date_fin = models.DateTimeField(
        _('Date de fin'),
        help_text="Date et heure de fin de l'événement"
    )
    
    # Localisation
    lieu = models.CharField(
        _('Lieu'),
        max_length=300,
        help_text="Nom du lieu de l'événement"
    )
    
    adresse = models.TextField(
        _('Adresse'),
        help_text="Adresse complète du lieu"
    )
    
    latitude = models.DecimalField(
        _('Latitude'),
        max_digits=10,
        decimal_places=8,
        null=True,
        blank=True,
        help_text="Coordonnée latitude pour la carte"
    )
    
    longitude = models.DecimalField(
        _('Longitude'),
        max_digits=11,
        decimal_places=8,
        null=True,
        blank=True,
        help_text="Coordonnée longitude pour la carte"
    )
    
    lien_google_maps = models.URLField(
        _('Lien Google Maps'),
        blank=True,
        help_text="Lien vers Google Maps pour le lieu"
    )
    
    # Relations
    createur = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='events_created',
        verbose_name=_('Créateur'),
        help_text="Utilisateur qui a créé l'événement"
    )
    
    # Relation avec l'entité (si l'événement est créé par une organisation)
    entite_organisatrice = models.ForeignKey(
        Entity,  # Référence au modèle Entity que nous avons créé
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='events_created',
        verbose_name=_('Entité organisatrice'),
        help_text="Organisation qui organise l'événement (optionnel)"
    )
    
    categorie = models.ForeignKey(
        EventCategory,
        on_delete=models.SET_NULL,
        null=True,
        related_name='events',
        verbose_name=_('Catégorie'),
        help_text="Catégorie de l'événement"
    )
    
    # Accès et tarification
    type_acces = models.CharField(
        _('Type d\'accès'),
        max_length=20,
        choices=TYPE_ACCES_CHOICES,
        default='GRATUIT',
        help_text="Type d'accès à l'événement"
    )
    
    prix = models.DecimalField(
        _('Prix'),
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Prix d'entrée en FCFA"
    )
    
    capacite_max = models.PositiveIntegerField(
        _('Capacité maximale'),
        null=True,
        blank=True,
        help_text="Nombre maximum de participants (optionnel)"
    )
    
    # Statut et validation
    statut = models.CharField(
        _('Statut'),
        max_length=20,
        choices=STATUT_CHOICES,
        default='BROUILLON',
        help_text="Statut de l'événement"
    )
    
    date_validation = models.DateTimeField(
        _('Date de validation'),
        null=True,
        blank=True,
        help_text="Date de validation par un administrateur"
    )
    
    validateur = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='events_validated',
        verbose_name=_('Validateur'),
        help_text="Administrateur qui a validé l'événement"
    )
    
    commentaire_validation = models.TextField(
        _('Commentaire de validation'),
        blank=True,
        help_text="Commentaire de l'administrateur"
    )
    
    # Statistiques
    nombre_vues = models.PositiveIntegerField(
        _('Nombre de vues'),
        default=0,
        help_text="Nombre de fois que l'événement a été consulté"
    )
    
    nombre_partages = models.PositiveIntegerField(
        _('Nombre de partages'),
        default=0,
        help_text="Nombre de fois que l'événement a été partagé"
    )
    
    # Métadonnées
    date_creation = models.DateTimeField(
        _('Date de création'),
        auto_now_add=True,
        help_text="Date de création de l'événement"
    )
    
    date_modification = models.DateTimeField(
        _('Date de modification'),
        auto_now=True,
        help_text="Date de dernière modification"
    )
    
    # Billetterie
    billetterie_activee = models.BooleanField(
        _('Billetterie activée'),
        default=False,
        help_text="Utiliser le système de billetterie intégré"
    )

    lien_billetterie_externe = models.URLField(
        _('Lien billetterie externe'),
        blank=True,
        help_text="Lien vers une billetterie externe si vous n'utilisez pas le système intégré"
    )
    
    commission_billetterie = models.DecimalField(
        _('Commission billetterie'),
        max_digits=5,
        decimal_places=2,
        default=10.00,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Commission en pourcentage sur les ventes"
    )
    
    class Meta:
        verbose_name = _('Événement')
        verbose_name_plural = _('Événements')
        ordering = ['-date_creation']
        indexes = [
            models.Index(fields=['statut', 'date_debut']),
            models.Index(fields=['createur', 'statut']),
            models.Index(fields=['categorie', 'statut']),
            models.Index(fields=['entite_organisatrice', 'statut']),
        ]
    
    def __str__(self):
        """Représentation string de l'événement."""
        return f"{self.titre} - {self.date_debut.strftime('%d/%m/%Y')}"
    
    def save(self, *args, **kwargs):
        """Sauvegarde personnalisée."""
        # Marquer comme terminé si la date est passée
        if self.date_fin < timezone.now() and self.statut == 'VALIDE':
            self.statut = 'TERMINE'
        
        super().save(*args, **kwargs)
    
    # === NOUVELLES MÉTHODES POUR LA GESTION DES MÉDIAS ===
    
    def get_image_couverture(self):
        """Retourne l'image de couverture principal de l'événement."""
        return self.medias.filter(
            usage='couverture',
            type_media='image',
            est_active=True
        ).first()
    
    def get_post_cover_image(self):
        """Retourne l'image de couverture pour les posts."""
        # D'abord chercher une image spécifique pour les posts
        post_cover = self.medias.filter(
            usage='post_cover',
            type_media='image',
            est_active=True
        ).first()
        
        # Sinon utiliser l'image de couverture principale
        if not post_cover:
            post_cover = self.get_image_couverture()
        
        return post_cover
    
    def get_galerie_images(self):
        """Retourne toutes les images de la galerie."""
        return self.medias.filter(
            usage='galerie',
            type_media='image',
            est_active=True
        ).order_by('ordre')
    
    def get_galerie_videos(self):
        """Retourne toutes les vidéos de la galerie."""
        return self.medias.filter(
            usage='galerie',
            type_media='video',
            est_active=True
        ).order_by('ordre')
    
    def get_all_medias(self):
        """Retourne tous les médias actifs triés par ordre."""
        return self.medias.filter(est_active=True).order_by('ordre')
    
    def get_medias_count(self):
        """Retourne le nombre total de médias."""
        return self.medias.filter(est_active=True).count()
    
    def has_cover_image(self):
        """Vérifie si l'événement a une image de couverture."""
        return self.get_image_couverture() is not None
    
    def has_post_cover(self):
        """Vérifie si l'événement a une image de couverture pour les posts."""
        return self.get_post_cover_image() is not None
    
    def add_media(self, fichier, type_media='image', usage='galerie', titre='', description='', user=None):
        """
        Méthode helper pour ajouter un média à l'événement.
        """
        ordre = self.medias.filter(usage=usage).count() + 1
        
        media = EventMedia.objects.create(
            evenement=self,
            fichier=fichier,
            type_media=type_media,
            usage=usage,
            titre=titre,
            description=description,
            ordre=ordre,
            uploade_par=user or self.createur
        )
        
        return media
    
    def set_cover_image(self, media_id):
        """
        Définit un média existant comme image de couverture.
        """
        try:
            media = self.medias.get(id=media_id, type_media='image')
            
            # Retirer le statut de couverture des autres médias
            self.medias.filter(usage='couverture').update(usage='galerie')
            
            # Définir le nouveau média comme couverture
            media.usage = 'couverture'
            media.save()
            
            return True
        except EventMedia.DoesNotExist:
            return False
    
    def set_post_cover_image(self, media_id):
        """
        Définit un média existant comme image de couverture pour les posts.
        """
        try:
            media = self.medias.get(id=media_id, type_media='image')
            
            # Retirer le statut de post_cover des autres médias
            self.medias.filter(usage='post_cover').update(usage='galerie')
            
            # Définir le nouveau média comme couverture de post
            media.usage = 'post_cover'
            media.save()
            
            return True
        except EventMedia.DoesNotExist:
            return False
    
    # === MÉTHODES EXISTANTES (conservées) ===
    
    def get_participants_count(self):
        """Retourne le nombre de participants à l'événement."""
        return self.participations.filter(statut='PARTICIPE').count()
    
    def get_interested_count(self):
        """Retourne le nombre d'utilisateurs intéressés."""
        return self.participations.filter(statut='INTERESSE').count()
    
    def is_full(self):
        """Vérifie si l'événement est complet."""
        if not self.capacite_max:
            return False
        return self.get_participants_count() >= self.capacite_max
    
    def is_past(self):
        """Vérifie si l'événement est passé."""
        return self.date_fin < timezone.now()
    
    def can_participate(self, user):
        """Vérifie si un utilisateur peut participer à l'événement."""
        if self.is_past() or self.statut != 'VALIDE':
            return False
        
        if self.is_full():
            return False
        
        # Vérifier si l'utilisateur n'est pas déjà inscrit
        return not self.participations.filter(
            utilisateur=user,
            statut__in=['PARTICIPE', 'INTERESSE']
        ).exists()
    
    def get_revenue(self):
        """Calcule le revenu total de l'événement."""
        if not self.billetterie_activee:
            return 0
        
        total = self.tickets.filter(statut='PAYE').aggregate(
            total=models.Sum('prix')
        )['total'] or 0
        
        return total
    
    def get_commission_amount(self):
        """Calcule le montant de commission sur les ventes."""
        revenue = self.get_revenue()
        return revenue * (self.commission_billetterie / 100)
    
    def get_organizer_name(self):
        """Retourne le nom de l'organisateur (utilisateur ou entité)."""
        if self.entite_organisatrice:
            return self.entite_organisatrice.nom
        return self.createur.get_full_name() or self.createur.username
    
    def is_organized_by_entity(self):
        """Vérifie si l'événement est organisé par une entité."""
        return self.entite_organisatrice is not None


class EventParticipation(models.Model):
    """
    Modèle pour la participation aux événements.
    
    Gère les différents types de participation :
    - Intéressé (like)
    - Participe (inscription confirmée)
    - A participé (après l'événement)
    """
    
    STATUT_CHOICES = [
        ('INTERESSE', _('Intéressé')),
        ('PARTICIPE', _('Participe')),
        ('A_PARTICIPE', _('A participé')),
        ('ANNULE', _('Annulé')),
    ]
    
    utilisateur = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='participations',
        verbose_name=_('Utilisateur'),
        help_text="Utilisateur participant"
    )
    
    evenement = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='participations',
        verbose_name=_('Événement'),
        help_text="Événement concerné"
    )
    
    statut = models.CharField(
        _('Statut'),
        max_length=20,
        choices=STATUT_CHOICES,
        default='INTERESSE',
        help_text="Type de participation"
    )
    
    date_participation = models.DateTimeField(
        _('Date de participation'),
        auto_now_add=True,
        help_text="Date d'inscription à l'événement"
    )
    
    date_modification = models.DateTimeField(
        _('Date de modification'),
        auto_now=True,
        help_text="Date de dernière modification du statut"
    )
    
    commentaire = models.TextField(
        _('Commentaire'),
        blank=True,
        help_text="Commentaire du participant"
    )
    
    class Meta:
        verbose_name = _('Participation à un événement')
        verbose_name_plural = _('Participations aux événements')
        unique_together = ['utilisateur', 'evenement']
        ordering = ['-date_participation']
    
    def __str__(self):
        """Représentation string de la participation."""
        return f"{self.utilisateur.username} - {self.evenement.titre} ({self.statut})"


class EventShare(models.Model):
    """
    Modèle pour le partage d'événements sur les réseaux sociaux.
    
    Suit les partages d'événements et génère des liens personnalisés
    pour augmenter la visibilité de la plateforme.
    """
    
    PLATEFORME_CHOICES = [
        ('FACEBOOK', _('Facebook')),
        ('TWITTER', _('Twitter')),
        ('INSTAGRAM', _('Instagram')),
        ('WHATSAPP', _('WhatsApp')),
        ('LINKEDIN', _('LinkedIn')),
        ('EMAIL', _('Email')),
        ('LIEN', _('Lien direct')),
    ]
    
    utilisateur = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='partages',
        verbose_name=_('Utilisateur'),
        help_text="Utilisateur qui partage"
    )
    
    evenement = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='partages',
        verbose_name=_('Événement'),
        help_text="Événement partagé"
    )
    
    plateforme = models.CharField(
        _('Plateforme'),
        max_length=20,
        choices=PLATEFORME_CHOICES,
        help_text="Plateforme de partage"
    )
    
    date_partage = models.DateTimeField(
        _('Date de partage'),
        auto_now_add=True,
        help_text="Date du partage"
    )
    
    lien_genere = models.URLField(
        _('Lien généré'),
        blank=True,
        help_text="Lien personnalisé généré pour le partage"
    )
    
    nombre_clics = models.PositiveIntegerField(
        _('Nombre de clics'),
        default=0,
        help_text="Nombre de clics sur le lien partagé"
    )
    
    class Meta:
        verbose_name = _('Partage d\'événement')
        verbose_name_plural = _('Partages d\'événement')
        ordering = ['-date_partage']
    
    def __str__(self):
        """Représentation string du partage."""
        return f"{self.utilisateur.username} partage {self.evenement.titre} sur {self.plateforme}"


class EventTicket(models.Model):
    """
    Modèle fusionné :
    - Définit les catégories de billets (ancien TicketType)
    - Gère les billets vendus (ancien EventTicket)
    """

    # Statuts possibles pour un billet acheté
    STATUT_CHOICES = [
        ('EN_ATTENTE', _('En attente de paiement')),
        ('PAYE', _('Payé')),
        ('ANNULE', _('Annulé')),
        ('REMBOURSE', _('Remboursé')),
        ('UTILISE', _('Utilisé')),
    ]

    # Liens
    evenement = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='tickets',
        verbose_name=_('Événement'),
        help_text="Événement concerné"
    )

    utilisateur = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='tickets',
        verbose_name=_('Utilisateur'),
        help_text="Acheteur du billet (si acheté)"
    )

    # Informations de catégorie (ex-TicketType)
    nom = models.CharField(
        _('Nom du ticket'),
        max_length=100,
        help_text="Nom de la catégorie (ex: Premium, Gold, Standard)"
    )

    description = models.TextField(
        _('Description'),
        blank=True,
        help_text="Détails sur cette catégorie de billet"
    )

    prix = models.DecimalField(
        _('Prix'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Prix unitaire en FCFA"
    )

    quantite_disponible = models.PositiveIntegerField(
        _('Quantité disponible'),
        help_text="Nombre total de billets disponibles pour ce type"
    )

    quantite_vendue = models.PositiveIntegerField(
        _('Quantité vendue'),
        default=0,
        help_text="Nombre de billets déjà vendus"
    )

    date_debut_vente = models.DateTimeField(
        _('Début des ventes'),
        null=True,
        blank=True,
        help_text="Date à partir de laquelle ce ticket est en vente"
    )

    date_fin_vente = models.DateTimeField(
        _('Fin des ventes'),
        null=True,
        blank=True,
        help_text="Date de fin de disponibilité"
    )

    actif = models.BooleanField(
        _('Actif'),
        default=True,
        help_text="Ce type de billet est-il actif ?"
    )

    # Informations spécifiques à un billet acheté
    uuid = models.UUIDField(
        _('Identifiant unique'),
        default=uuid.uuid4,
        editable=False,
        unique=True,
        help_text="Identifiant unique du billet"
    )

    quantite = models.PositiveIntegerField(
        _('Quantité'),
        default=1,
        help_text="Nombre de billets achetés dans cette commande"
    )

    statut = models.CharField(
        _('Statut'),
        max_length=20,
        choices=STATUT_CHOICES,
        default='EN_ATTENTE',
        help_text="Statut du billet"
    )

    code_qr = models.ImageField(
        _('Code QR'),
        upload_to='tickets/qr/',
        blank=True,
        help_text="Code QR pour la validation"
    )

    date_achat = models.DateTimeField(
        _('Date d\'achat'),
        auto_now_add=True,
        help_text="Date d'achat du billet"
    )

    date_utilisation = models.DateTimeField(
        _('Date d\'utilisation'),
        null=True,
        blank=True,
        help_text="Date d'utilisation du billet"
    )

    reference_paiement = models.CharField(
        _('Référence de paiement'),
        max_length=100,
        blank=True,
        help_text="Référence du paiement Mobile Money"
    )

    class Meta:
        verbose_name = _('Billet d\'événement')
        verbose_name_plural = _('Billets d\'événement')
        ordering = ['prix', '-date_achat']

    def __str__(self):
        return f"{self.nom} - {self.prix} FCFA - {self.evenement.titre}"

    # Vérifie la disponibilité (ex-TicketType.disponible)
    def disponible(self):
        if not self.actif:
            return False
        if self.quantite_vendue >= self.quantite_disponible:
            return False
        now = timezone.now()
        if self.date_debut_vente and now < self.date_debut_vente:
            return False
        if self.date_fin_vente and now > self.date_fin_vente:
            return False
        return True

    # Prix total (ex-EventTicket)
    def get_total_price(self):
        return self.prix * self.quantite

    # Vérifie si le billet peut être utilisé
    def can_be_used(self):
        return (
            self.statut == 'PAYE' and
            not self.evenement.is_past() and
            self.evenement.statut == 'VALIDE'
        )

    # Sauvegarde avec génération de QR code
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.statut == 'PAYE' and not self.code_qr:
            self.generate_qr_code()

    def generate_qr_code(self):
        qr_data = f"SPOTVIBE-{self.uuid}-{self.evenement.id}"
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        filename = f"qr_{self.uuid}.png"
        self.code_qr.save(filename, File(buffer), save=True)
        buffer.close()
