"""
Services pour l'application subscriptions.

Ce module contient la logique métier pour les abonnements.
"""

from django.utils import timezone
from django.db.models import Count, Sum
from datetime import timedelta
import logging

from .models import Subscription, SubscriptionHistory
from apps.events.models import Event, EventParticipation

logger = logging.getLogger(__name__)


class SubscriptionService:
    """Service principal pour la gestion des abonnements."""
    
    def activate_subscription(self, subscription):
        """Active un abonnement après paiement réussi."""
        try:
            # Désactiver les anciens abonnements actifs
            Subscription.objects.filter(
                utilisateur=subscription.utilisateur,
                statut='ACTIF'
            ).update(statut='REMPLACE')
            
            # Activer le nouvel abonnement
            subscription.statut = 'ACTIF'
            subscription.save()
            
            # Créer l'entrée d'historique
            SubscriptionHistory.objects.create(
                utilisateur=subscription.utilisateur,
                plan=subscription.plan,
                action='ACTIVATION',
                date_debut=subscription.date_debut,
                date_fin=subscription.date_fin,
                montant_paye=subscription.plan.prix,
                reference_paiement=subscription.reference_paiement,
                details={
                    'subscription_id': subscription.id,
                    'activation_date': timezone.now().isoformat()
                }
            )
            
            # Appliquer les avantages du plan
            self._apply_plan_benefits(subscription)
            
            return {
                'success': True,
                'subscription': subscription
            }
            
        except Exception as e:
            logger.error(f'Subscription activation error: {e}')
            return {
                'success': False,
                'error': str(e)
            }
    
    def renew_subscription(self, subscription, new_plan=None):
        """Renouvelle un abonnement."""
        try:
            plan = new_plan or subscription.plan
            
            # Calculer les nouvelles dates
            if subscription.statut == 'ACTIF':
                # Renouvellement avant expiration
                date_debut = subscription.date_fin
            else:
                # Renouvellement après expiration
                date_debut = timezone.now().date()
            
            date_fin = date_debut + timedelta(days=plan.duree_jours)
            
            # Créer le nouvel abonnement
            new_subscription = Subscription.objects.create(
                utilisateur=subscription.utilisateur,
                plan=plan,
                date_debut=date_debut,
                date_fin=date_fin,
                statut='EN_ATTENTE',  # En attente de paiement
                renouvellement_auto=subscription.renouvellement_auto
            )
            
            # Marquer l'ancien comme remplacé
            subscription.statut = 'REMPLACE'
            subscription.save()
            
            return {
                'success': True,
                'subscription': new_subscription
            }
            
        except Exception as e:
            logger.error(f'Subscription renewal error: {e}')
            return {
                'success': False,
                'error': str(e)
            }
    
    def cancel_subscription(self, subscription, reason='', cancel_immediately=False):
        """Annule un abonnement."""
        try:
            if cancel_immediately:
                # Annulation immédiate
                subscription.statut = 'ANNULE'
                subscription.date_fin = timezone.now().date()
            else:
                # Annulation à la fin de la période
                subscription.renouvellement_auto = False
            
            subscription.save()
            
            # Créer l'entrée d'historique
            SubscriptionHistory.objects.create(
                utilisateur=subscription.utilisateur,
                plan=subscription.plan,
                action='ANNULATION',
                date_debut=subscription.date_debut,
                date_fin=subscription.date_fin,
                details={
                    'subscription_id': subscription.id,
                    'reason': reason,
                    'immediate': cancel_immediately,
                    'cancellation_date': timezone.now().isoformat()
                }
            )
            
            return {'success': True}
            
        except Exception as e:
            logger.error(f'Subscription cancellation error: {e}')
            return {
                'success': False,
                'error': str(e)
            }
    
    def upgrade_subscription(self, subscription, new_plan):
        """Met à niveau un abonnement."""
        try:
            # Calculer le montant au prorata
            days_remaining = (subscription.date_fin - timezone.now().date()).days
            if days_remaining <= 0:
                return {
                    'success': False,
                    'error': 'Abonnement expiré, veuillez renouveler'
                }
            
            # Calculer le crédit restant
            daily_rate_old = subscription.plan.prix / subscription.plan.duree_jours
            credit_remaining = daily_rate_old * days_remaining
            
            # Calculer le coût du nouveau plan au prorata
            daily_rate_new = new_plan.prix / new_plan.duree_jours
            cost_new = daily_rate_new * days_remaining
            
            amount_due = cost_new - credit_remaining
            
            if amount_due > 0:
                # Paiement supplémentaire requis
                # Créer un nouvel abonnement en attente
                new_subscription = Subscription.objects.create(
                    utilisateur=subscription.utilisateur,
                    plan=new_plan,
                    date_debut=timezone.now().date(),
                    date_fin=subscription.date_fin,
                    statut='EN_ATTENTE',
                    renouvellement_auto=subscription.renouvellement_auto
                )
                
                return {
                    'success': True,
                    'subscription': new_subscription,
                    'payment_required': True,
                    'amount_due': amount_due
                }
            else:
                # Pas de paiement supplémentaire, mise à niveau immédiate
                subscription.plan = new_plan
                subscription.save()
                
                # Créer l'entrée d'historique
                SubscriptionHistory.objects.create(
                    utilisateur=subscription.utilisateur,
                    plan=new_plan,
                    action='MISE_A_NIVEAU',
                    date_debut=subscription.date_debut,
                    date_fin=subscription.date_fin,
                    details={
                        'subscription_id': subscription.id,
                        'old_plan': subscription.plan.nom,
                        'new_plan': new_plan.nom,
                        'upgrade_date': timezone.now().isoformat()
                    }
                )
                
                return {
                    'success': True,
                    'subscription': subscription,
                    'payment_required': False
                }
                
        except Exception as e:
            logger.error(f'Subscription upgrade error: {e}')
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_usage_stats(self, subscription):
        """Obtient les statistiques d'utilisation d'un abonnement."""
        try:
            user = subscription.utilisateur
            plan = subscription.plan
            
            # Événements créés ce mois
            current_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            events_created = Event.objects.filter(
                organisateur=user,
                date_creation__gte=current_month
            ).count()
            
            # Participants total ce mois
            participants_total = EventParticipation.objects.filter(
                evenement__organisateur=user,
                date_participation__gte=current_month
            ).count()
            
            # Photos uploadées (simulation)
            photos_uploaded = events_created * 3  # Moyenne de 3 photos par événement
            
            # Calcul du pourcentage d'utilisation
            usage_events = (events_created / plan.limite_evenements) * 100 if plan.limite_evenements > 0 else 0
            usage_participants = (participants_total / plan.limite_participants) * 100 if plan.limite_participants > 0 else 0
            usage_photos = (photos_uploaded / plan.limite_photos) * 100 if plan.limite_photos > 0 else 0
            
            usage_percentage = max(usage_events, usage_participants, usage_photos)
            
            # Avertissements
            warnings = []
            if usage_events > 80:
                warnings.append(f"Vous avez utilisé {usage_events:.0f}% de votre limite d'événements")
            if usage_participants > 80:
                warnings.append(f"Vous avez utilisé {usage_participants:.0f}% de votre limite de participants")
            if usage_photos > 80:
                warnings.append(f"Vous avez utilisé {usage_photos:.0f}% de votre limite de photos")
            
            return {
                'events_created': events_created,
                'events_limit': plan.limite_evenements,
                'participants_total': participants_total,
                'participants_limit': plan.limite_participants,
                'photos_uploaded': photos_uploaded,
                'photos_limit': plan.limite_photos,
                'usage_percentage': usage_percentage,
                'warnings': warnings
            }
            
        except Exception as e:
            logger.error(f'Usage stats error: {e}')
            return {
                'events_created': 0,
                'events_limit': 0,
                'participants_total': 0,
                'participants_limit': 0,
                'photos_uploaded': 0,
                'photos_limit': 0,
                'usage_percentage': 0,
                'warnings': []
            }
    
    def check_subscription_limits(self, user, action_type):
        """Vérifie si l'utilisateur peut effectuer une action selon son abonnement."""
        try:
            # Obtenir l'abonnement actif
            subscription = Subscription.objects.filter(
                utilisateur=user,
                statut='ACTIF'
            ).first()
            
            if not subscription:
                # Utilisateur gratuit - limites de base
                limits = {
                    'events': 2,
                    'participants': 50,
                    'photos': 10
                }
            else:
                limits = {
                    'events': subscription.plan.limite_evenements,
                    'participants': subscription.plan.limite_participants,
                    'photos': subscription.plan.limite_photos
                }
            
            # Vérifier selon le type d'action
            if action_type == 'create_event':
                current_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                events_count = Event.objects.filter(
                    organisateur=user,
                    date_creation__gte=current_month
                ).count()
                
                return {
                    'allowed': events_count < limits['events'],
                    'current': events_count,
                    'limit': limits['events'],
                    'message': f"Vous avez créé {events_count}/{limits['events']} événements ce mois"
                }
            
            elif action_type == 'add_participant':
                # Vérifier pour un événement spécifique
                return {
                    'allowed': True,  # À implémenter selon l'événement
                    'limit': limits['participants']
                }
            
            elif action_type == 'upload_photo':
                return {
                    'allowed': True,  # À implémenter
                    'limit': limits['photos']
                }
            
            return {'allowed': True}
            
        except Exception as e:
            logger.error(f'Subscription limits check error: {e}')
            return {'allowed': False, 'error': str(e)}
    
    def _apply_plan_benefits(self, subscription):
        """Applique les avantages du plan à l'utilisateur."""
        try:
            user = subscription.utilisateur
            plan = subscription.plan
            
            # Badge vérifié
            if plan.badge_verifie and not user.est_verifie:
                user.est_verifie = True
                user.save()
            
            # Autres avantages à implémenter selon les besoins
            
        except Exception as e:
            logger.error(f'Apply plan benefits error: {e}')
    
    def process_expired_subscriptions(self):
        """Traite les abonnements expirés (tâche périodique)."""
        try:
            today = timezone.now().date()
            
            # Marquer les abonnements expirés
            expired_subscriptions = Subscription.objects.filter(
                statut='ACTIF',
                date_fin__lt=today
            )
            
            for subscription in expired_subscriptions:
                if subscription.renouvellement_auto:
                    # Tenter le renouvellement automatique
                    self._auto_renew_subscription(subscription)
                else:
                    # Marquer comme expiré
                    subscription.statut = 'EXPIRE'
                    subscription.save()
                    
                    # Créer l'entrée d'historique
                    SubscriptionHistory.objects.create(
                        utilisateur=subscription.utilisateur,
                        plan=subscription.plan,
                        action='EXPIRATION',
                        date_debut=subscription.date_debut,
                        date_fin=subscription.date_fin,
                        details={
                            'subscription_id': subscription.id,
                            'expiration_date': today.isoformat()
                        }
                    )
            
            return {
                'success': True,
                'processed': expired_subscriptions.count()
            }
            
        except Exception as e:
            logger.error(f'Process expired subscriptions error: {e}')
            return {
                'success': False,
                'error': str(e)
            }
    
    def _auto_renew_subscription(self, subscription):
        """Renouvelle automatiquement un abonnement."""
        try:
            # Créer le nouvel abonnement
            new_subscription = Subscription.objects.create(
                utilisateur=subscription.utilisateur,
                plan=subscription.plan,
                date_debut=subscription.date_fin,
                date_fin=subscription.date_fin + timedelta(days=subscription.plan.duree_jours),
                statut='EN_ATTENTE',
                renouvellement_auto=True
            )
            
            # Marquer l'ancien comme remplacé
            subscription.statut = 'REMPLACE'
            subscription.save()
            
            # Ici, vous devriez déclencher le processus de paiement automatique
            # Pour l'exemple, nous simulons un paiement réussi
            self.activate_subscription(new_subscription)
            
        except Exception as e:
            logger.error(f'Auto renewal error: {e}')
            # En cas d'échec, marquer comme expiré
            subscription.statut = 'EXPIRE'
            subscription.save()

