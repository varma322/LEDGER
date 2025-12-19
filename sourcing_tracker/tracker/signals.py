from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from decimal import Decimal
from .models import Transaction, Deal


@receiver(post_save, sender=Transaction)
def update_partner_balance_on_transaction(sender, instance, created, **kwargs):
    """
    Update Partner's current_balance when a Transaction is saved.
    - ADVANCE_RECEIVED: Add to balance
    - REFUND_GIVEN: Subtract from balance
    """
    if created:
        partner = instance.partner
        if instance.transaction_type == 'ADVANCE_RECEIVED':
            partner.current_balance += instance.amount
        elif instance.transaction_type == 'REFUND_GIVEN':
            partner.current_balance -= instance.amount
        partner.save(update_fields=['current_balance'])


@receiver(pre_save, sender=Deal)
def store_previous_actual_cost(sender, instance, **kwargs):
    """Store the previous actual_cost value before saving."""
    if instance.pk:
        try:
            old_instance = Deal.objects.get(pk=instance.pk)
            instance._previous_actual_cost = old_instance.actual_cost
            instance._previous_cost_deducted = old_instance.cost_deducted
        except Deal.DoesNotExist:
            instance._previous_actual_cost = None
            instance._previous_cost_deducted = False
    else:
        instance._previous_actual_cost = None
        instance._previous_cost_deducted = False


@receiver(post_save, sender=Deal)
def update_partner_balance_on_deal(sender, instance, created, **kwargs):
    """
    Update Partner's current_balance when a Deal's actual_cost is set.
    Subtract the actual_cost from the partner's balance only once.
    """
    partner = instance.partner
    
    # Check if this is the first time actual_cost is being set
    if instance.actual_cost and not instance.cost_deducted:
        # Deduct the actual_cost from partner balance
        partner.current_balance -= instance.actual_cost
        partner.save(update_fields=['current_balance'])
        
        # Mark as deducted (avoid recursive save by using update)
        Deal.objects.filter(pk=instance.pk).update(cost_deducted=True)
    
    # Handle case where actual_cost is updated after initial deduction
    elif instance.actual_cost and hasattr(instance, '_previous_actual_cost'):
        previous_cost = instance._previous_actual_cost or Decimal('0.00')
        if instance._previous_cost_deducted and instance.actual_cost != previous_cost:
            # Refund the old cost and deduct the new cost
            cost_difference = instance.actual_cost - previous_cost
            partner.current_balance -= cost_difference
            partner.save(update_fields=['current_balance'])
