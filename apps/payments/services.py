"""
Services pour l'application payments.

Ce module contient la logique métier pour les paiements Mobile Money.
"""

import requests
import logging
import uuid
from decimal import Decimal
from django.conf import settings
from django.utils import timezone
from .models import Payment, MomoTransaction, Commission

logger = logging.getLogger(__name__)


class PaymentService:
    """Service principal pour la gestion des paiements."""
    
    def initiate_payment(self, payment):
        """Initie un paiement selon la méthode choisie."""
        try:
            if payment.methode_paiement == 'ORANGE_MONEY':
                return self._initiate_orange_money(payment)
            elif payment.methode_paiement == 'MTN_MONEY':
                return self._initiate_mtn_money(payment)
            elif payment.methode_paiement == 'MOOV_MONEY':
                return self._initiate_moov_money(payment)
            else:
                return {
                    'success': False,
                    'error': 'Méthode de paiement non supportée'
                }
        except Exception as e:
            logger.error(f'Payment initiation error: {e}')
            return {
                'success': False,
                'error': str(e)
            }
    
    def _initiate_orange_money(self, payment):
        """Initie un paiement Orange Money."""
        # Configuration Orange Money
        api_key = getattr(settings, 'ORANGE_MONEY_API_KEY', 'test_key')
        merchant_key = getattr(settings, 'ORANGE_MONEY_MERCHANT_KEY', 'test_merchant')
        base_url = getattr(settings, 'ORANGE_MONEY_BASE_URL', 'https://api.orange.com/orange-money-webpay/dev/v1')
        
        # Données de la transaction
        transaction_data = {
            'merchant_key': merchant_key,
            'currency': payment.devise,
            'order_id': str(payment.uuid),
            'amount': int(payment.montant),
            'return_url': f"{settings.DOMAIN}/payment/success/",
            'cancel_url': f"{settings.DOMAIN}/payment/cancel/",
            'notif_url': f"{settings.DOMAIN}/api/payments/webhooks/orange/",
            'lang': 'fr',
            'reference': f"SPOTVIBE-{payment.id}"
        }
        
        try:
            # Simulation d'appel API (remplacez par l'API réelle)
            # response = requests.post(
            #     f"{base_url}/webpayment",
            #     json=transaction_data,
            #     headers={'Authorization': f'Bearer {api_key}'}
            # )
            
            # Simulation de réponse
            transaction_id = f"OM_{uuid.uuid4().hex[:10]}"
            
            # Créer la transaction
            momo_transaction = MomoTransaction.objects.create(
                payment=payment,
                provider='ORANGE_MONEY',
                transaction_id=transaction_id,
                amount=payment.montant,
                currency=payment.devise,
                phone_number=payment.telephone_paiement,
                status='PENDING'
            )
            
            return {
                'success': True,
                'data': {
                    'transaction_id': transaction_id,
                    'payment_url': f"{base_url}/webpayment/{transaction_id}",
                    'status': 'PENDING'
                }
            }
            
        except Exception as e:
            logger.error(f'Orange Money API error: {e}')
            return {
                'success': False,
                'error': 'Erreur lors de la communication avec Orange Money'
            }
    
    def _initiate_mtn_money(self, payment):
        """Initie un paiement MTN Money."""
        # Configuration MTN Money
        api_key = getattr(settings, 'MTN_MONEY_API_KEY', 'test_key')
        subscription_key = getattr(settings, 'MTN_MONEY_SUBSCRIPTION_KEY', 'test_sub')
        base_url = getattr(settings, 'MTN_MONEY_BASE_URL', 'https://sandbox.momodeveloper.mtn.com')
        
        # Données de la transaction
        transaction_data = {
            'amount': str(payment.montant),
            'currency': payment.devise,
            'externalId': str(payment.uuid),
            'payer': {
                'partyIdType': 'MSISDN',
                'partyId': payment.telephone_paiement.replace('+225', '225')
            },
            'payerMessage': payment.description or 'Paiement SpotVibe',
            'payeeNote': f'Paiement pour {payment.type_paiement}'
        }
        
        try:
            # Simulation d'appel API
            transaction_id = f"MTN_{uuid.uuid4().hex[:10]}"
            
            # Créer la transaction
            momo_transaction = MomoTransaction.objects.create(
                payment=payment,
                provider='MTN_MONEY',
                transaction_id=transaction_id,
                amount=payment.montant,
                currency=payment.devise,
                phone_number=payment.telephone_paiement,
                status='PENDING'
            )
            
            return {
                'success': True,
                'data': {
                    'transaction_id': transaction_id,
                    'status': 'PENDING',
                    'message': 'Vérifiez votre téléphone pour confirmer le paiement'
                }
            }
            
        except Exception as e:
            logger.error(f'MTN Money API error: {e}')
            return {
                'success': False,
                'error': 'Erreur lors de la communication avec MTN Money'
            }
    
    def _initiate_moov_money(self, payment):
        """Initie un paiement Moov Money."""
        # Configuration Moov Money
        api_key = getattr(settings, 'MOOV_MONEY_API_KEY', 'test_key')
        base_url = getattr(settings, 'MOOV_MONEY_BASE_URL', 'https://api.moov-africa.com')
        
        # Données de la transaction
        transaction_data = {
            'amount': float(payment.montant),
            'currency': payment.devise,
            'reference': str(payment.uuid),
            'subscriber': payment.telephone_paiement,
            'description': payment.description or 'Paiement SpotVibe'
        }
        
        try:
            # Simulation d'appel API
            transaction_id = f"MOOV_{uuid.uuid4().hex[:10]}"
            
            # Créer la transaction
            momo_transaction = MomoTransaction.objects.create(
                payment=payment,
                provider='MOOV_MONEY',
                transaction_id=transaction_id,
                amount=payment.montant,
                currency=payment.devise,
                phone_number=payment.telephone_paiement,
                status='PENDING'
            )
            
            return {
                'success': True,
                'data': {
                    'transaction_id': transaction_id,
                    'status': 'PENDING',
                    'message': 'Vérifiez votre téléphone pour confirmer le paiement'
                }
            }
            
        except Exception as e:
            logger.error(f'Moov Money API error: {e}')
            return {
                'success': False,
                'error': 'Erreur lors de la communication avec Moov Money'
            }
    
    def verify_payment(self, payment):
        """Vérifie le statut d'un paiement."""
        try:
            transaction = MomoTransaction.objects.filter(payment=payment).first()
            if not transaction:
                return {
                    'success': False,
                    'error': 'Transaction introuvable'
                }
            
            # Vérifier selon le provider
            if transaction.provider == 'ORANGE_MONEY':
                return self._verify_orange_money(transaction)
            elif transaction.provider == 'MTN_MONEY':
                return self._verify_mtn_money(transaction)
            elif transaction.provider == 'MOOV_MONEY':
                return self._verify_moov_money(transaction)
            
        except Exception as e:
            logger.error(f'Payment verification error: {e}')
            return {
                'success': False,
                'error': str(e)
            }
    
    def _verify_orange_money(self, transaction):
        """Vérifie un paiement Orange Money."""
        # Simulation de vérification
        return {
            'success': True,
            'status': transaction.status,
            'transaction_id': transaction.transaction_id
        }
    
    def _verify_mtn_money(self, transaction):
        """Vérifie un paiement MTN Money."""
        # Simulation de vérification
        return {
            'success': True,
            'status': transaction.status,
            'transaction_id': transaction.transaction_id
        }
    
    def _verify_moov_money(self, transaction):
        """Vérifie un paiement Moov Money."""
        # Simulation de vérification
        return {
            'success': True,
            'status': transaction.status,
            'transaction_id': transaction.transaction_id
        }
    
    def cancel_payment(self, payment, reason=''):
        """Annule un paiement."""
        try:
            transaction = MomoTransaction.objects.filter(payment=payment).first()
            if transaction:
                transaction.status = 'CANCELLED'
                transaction.error_message = reason
                transaction.save()
            
            return {'success': True}
            
        except Exception as e:
            logger.error(f'Payment cancellation error: {e}')
            return {'success': False, 'error': str(e)}


class MomoService:
    """Service pour traiter les webhooks Mobile Money."""
    
    def process_orange_webhook(self, webhook_data):
        """Traite un webhook Orange Money."""
        try:
            transaction_id = webhook_data['transaction_id']
            status = webhook_data['status']
            
            # Trouver la transaction
            transaction = MomoTransaction.objects.filter(
                transaction_id=transaction_id,
                provider='ORANGE_MONEY'
            ).first()
            
            if not transaction:
                return {
                    'success': False,
                    'error': 'Transaction introuvable'
                }
            
            # Mettre à jour le statut
            transaction.status = status
            transaction.callback_data = webhook_data
            transaction.save()
            
            # Mettre à jour le paiement
            payment = transaction.payment
            if status == 'SUCCESS':
                payment.statut = 'REUSSI'
                payment.date_completion = timezone.now()
                payment.reference_externe = webhook_data.get('reference', '')
                
                # Calculer et créer la commission
                self._create_commission(payment)
                
            elif status == 'FAILED':
                payment.statut = 'ECHEC'
                
            payment.save()
            
            return {'success': True}
            
        except Exception as e:
            logger.error(f'Orange webhook processing error: {e}')
            return {'success': False, 'error': str(e)}
    
    def process_mtn_webhook(self, webhook_data):
        """Traite un webhook MTN Money."""
        try:
            transaction_id = webhook_data['transaction_id']
            status = webhook_data['status']
            
            # Trouver la transaction
            transaction = MomoTransaction.objects.filter(
                transaction_id=transaction_id,
                provider='MTN_MONEY'
            ).first()
            
            if not transaction:
                return {
                    'success': False,
                    'error': 'Transaction introuvable'
                }
            
            # Mettre à jour le statut
            transaction.status = status
            transaction.callback_data = webhook_data
            transaction.save()
            
            # Mettre à jour le paiement
            payment = transaction.payment
            if status == 'SUCCESS':
                payment.statut = 'REUSSI'
                payment.date_completion = timezone.now()
                payment.reference_externe = webhook_data.get('reference', '')
                
                # Calculer et créer la commission
                self._create_commission(payment)
                
            elif status == 'FAILED':
                payment.statut = 'ECHEC'
                
            payment.save()
            
            return {'success': True}
            
        except Exception as e:
            logger.error(f'MTN webhook processing error: {e}')
            return {'success': False, 'error': str(e)}
    
    def process_moov_webhook(self, webhook_data):
        """Traite un webhook Moov Money."""
        try:
            transaction_id = webhook_data['transaction_id']
            status = webhook_data['status']
            
            # Trouver la transaction
            transaction = MomoTransaction.objects.filter(
                transaction_id=transaction_id,
                provider='MOOV_MONEY'
            ).first()
            
            if not transaction:
                return {
                    'success': False,
                    'error': 'Transaction introuvable'
                }
            
            # Mettre à jour le statut
            transaction.status = status
            transaction.callback_data = webhook_data
            transaction.save()
            
            # Mettre à jour le paiement
            payment = transaction.payment
            if status == 'SUCCESS':
                payment.statut = 'REUSSI'
                payment.date_completion = timezone.now()
                payment.reference_externe = webhook_data.get('reference', '')
                
                # Calculer et créer la commission
                self._create_commission(payment)
                
            elif status == 'FAILED':
                payment.statut = 'ECHEC'
                
            payment.save()
            
            return {'success': True}
            
        except Exception as e:
            logger.error(f'Moov webhook processing error: {e}')
            return {'success': False, 'error': str(e)}
    
    def _create_commission(self, payment):
        """Crée une commission pour un paiement réussi."""
        try:
            # Taux de commission selon le type
            commission_rates = {
                'BILLET': Decimal('0.05'),  # 5%
                'ABONNEMENT': Decimal('0.03'),  # 3%
                'COMMISSION': Decimal('0.00')  # Pas de commission sur les commissions
            }
            
            rate = commission_rates.get(payment.type_paiement, Decimal('0.05'))
            
            if rate > 0:
                commission_amount = payment.montant * rate
                
                Commission.objects.create(
                    payment=payment,
                    type_commission=payment.type_paiement,
                    montant_base=payment.montant,
                    pourcentage=rate,
                    montant_commission=commission_amount,
                    statut='EN_ATTENTE'
                )
                
        except Exception as e:
            logger.error(f'Commission creation error: {e}')


class RefundService:
    """Service pour la gestion des remboursements."""
    
    def process_refund(self, refund):
        """Traite une demande de remboursement."""
        try:
            payment = refund.payment
            
            # Vérifier les conditions de remboursement
            if not self._can_refund(payment):
                return {
                    'success': False,
                    'error': 'Ce paiement n\'est pas éligible au remboursement'
                }
            
            # Initier le remboursement selon la méthode
            if payment.methode_paiement == 'ORANGE_MONEY':
                return self._process_orange_refund(refund)
            elif payment.methode_paiement == 'MTN_MONEY':
                return self._process_mtn_refund(refund)
            elif payment.methode_paiement == 'MOOV_MONEY':
                return self._process_moov_refund(refund)
            
        except Exception as e:
            logger.error(f'Refund processing error: {e}')
            return {'success': False, 'error': str(e)}
    
    def _can_refund(self, payment):
        """Vérifie si un paiement peut être remboursé."""
        # Vérifier que le paiement est réussi
        if payment.statut != 'REUSSI':
            return False
        
        # Vérifier la date (par exemple, dans les 30 jours)
        days_since_payment = (timezone.now() - payment.date_completion).days
        if days_since_payment > 30:
            return False
        
        return True
    
    def _process_orange_refund(self, refund):
        """Traite un remboursement Orange Money."""
        # Simulation de remboursement
        refund.statut = 'APPROUVE'
        refund.date_traitement = timezone.now()
        refund.reference_remboursement = f"REF_OM_{uuid.uuid4().hex[:8]}"
        refund.save()
        
        return {'success': True}
    
    def _process_mtn_refund(self, refund):
        """Traite un remboursement MTN Money."""
        # Simulation de remboursement
        refund.statut = 'APPROUVE'
        refund.date_traitement = timezone.now()
        refund.reference_remboursement = f"REF_MTN_{uuid.uuid4().hex[:8]}"
        refund.save()
        
        return {'success': True}
    
    def _process_moov_refund(self, refund):
        """Traite un remboursement Moov Money."""
        # Simulation de remboursement
        refund.statut = 'APPROUVE'
        refund.date_traitement = timezone.now()
        refund.reference_remboursement = f"REF_MOOV_{uuid.uuid4().hex[:8]}"
        refund.save()
        
        return {'success': True}

