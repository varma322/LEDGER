from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum
from django.http import HttpResponse
from decimal import Decimal
from .models import Partner, Transaction, Deal
from .forms import (
    PartnerForm, TransactionForm, DealForm, 
    QuickAdvanceForm, DealStatusUpdateForm
)


def dashboard(request):
    """
    Dashboard view showing partner cards with balances and quick advance form.
    """
    partners = Partner.objects.all()
    
    # Calculate totals
    total_balance = partners.aggregate(total=Sum('current_balance'))['total'] or Decimal('0.00')
    active_deals_count = Deal.objects.exclude(status__in=['DELIVERED', 'RETURNED']).count()
    
    if request.method == 'POST':
        form = QuickAdvanceForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Advance added successfully!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Error adding advance. Please check the form.')
    else:
        form = QuickAdvanceForm()
    
    context = {
        'partners': partners,
        'form': form,
        'total_balance': total_balance,
        'active_deals_count': active_deals_count,
    }
    return render(request, 'tracker/dashboard.html', context)


def add_partner(request):
    """View for adding a new partner."""
    if request.method == 'POST':
        form = PartnerForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Partner added successfully!')
            return redirect('dashboard')
    else:
        form = PartnerForm()
    
    return render(request, 'tracker/add_partner.html', {'form': form})


def ledger(request):
    """
    Ledger view showing all transactions with filtering by partner.
    """
    transactions = Transaction.objects.select_related('partner').all()
    partners = Partner.objects.all()
    
    # Filter by partner if specified
    partner_id = request.GET.get('partner')
    if partner_id:
        transactions = transactions.filter(partner_id=partner_id)
    
    # Add new transaction
    if request.method == 'POST':
        form = TransactionForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Transaction recorded successfully!')
            return redirect('ledger')
        else:
            messages.error(request, 'Error recording transaction.')
    else:
        form = TransactionForm()
    
    context = {
        'transactions': transactions,
        'partners': partners,
        'form': form,
        'selected_partner': partner_id,
    }
    return render(request, 'tracker/ledger.html', context)


def procurement(request):
    """
    Procurement view showing active deals (SOURCING and BOOKED status).
    """
    active_deals = Deal.objects.filter(
        status__in=['SOURCING', 'BOOKED']
    ).select_related('partner')
    
    partners = Partner.objects.all()
    
    if request.method == 'POST':
        form = DealForm(request.POST, request.FILES)
        if form.is_valid():
            deal = form.save()
            messages.success(request, f'Deal for "{deal.item_name}" created successfully!')
            return redirect('procurement')
        else:
            messages.error(request, 'Error creating deal. Please check the form.')
    else:
        form = DealForm()
        # Default to SOURCING status for new deals
        form.initial['status'] = 'SOURCING'
    
    context = {
        'deals': active_deals,
        'partners': partners,
        'form': form,
    }
    return render(request, 'tracker/procurement.html', context)


def update_deal(request, deal_id):
    """View for updating a deal's details."""
    deal = get_object_or_404(Deal, id=deal_id)
    
    if request.method == 'POST':
        form = DealStatusUpdateForm(request.POST, request.FILES, instance=deal)
        if form.is_valid():
            # Validate: Vendor invoice required for BOOKED status
            new_status = form.cleaned_data.get('status')
            if new_status == 'BOOKED' and not deal.vendor_invoice and not form.cleaned_data.get('vendor_invoice'):
                messages.error(request, 'Vendor invoice is required to mark deal as Booked.')
                return redirect(request.META.get('HTTP_REFERER', 'procurement'))
            
            form.save()
            messages.success(request, f'Deal "{deal.item_name}" updated successfully!')
            
            # Redirect based on current page
            if deal.status in ['IN_WAREHOUSE', 'SHIPPED', 'DELIVERED']:
                return redirect('logistics')
            return redirect('procurement')
        else:
            messages.error(request, 'Error updating deal.')
    
    return redirect(request.META.get('HTTP_REFERER', 'procurement'))


def logistics(request):
    """
    Logistics view showing deals in warehouse or shipped status.
    """
    logistics_deals = Deal.objects.filter(
        status__in=['IN_WAREHOUSE', 'SHIPPED']
    ).select_related('partner')
    
    delivered_deals = Deal.objects.filter(
        status='DELIVERED'
    ).select_related('partner').order_by('-updated_at')[:10]
    
    context = {
        'deals': logistics_deals,
        'delivered_deals': delivered_deals,
    }
    return render(request, 'tracker/logistics.html', context)


def mark_delivered(request, deal_id):
    """Mark a deal as delivered."""
    deal = get_object_or_404(Deal, id=deal_id)
    
    if request.method == 'POST':
        deal.status = 'DELIVERED'
        deal.save()
        messages.success(request, f'Deal "{deal.item_name}" marked as delivered!')
    
    return redirect('logistics')


def generate_commission_invoice(request, deal_id):
    """Generate a simple commission invoice for a delivered deal."""
    deal = get_object_or_404(Deal, id=deal_id, status='DELIVERED')
    
    context = {
        'deal': deal,
        'commission_amount': deal.commission_amount,
    }
    return render(request, 'tracker/commission_invoice.html', context)


def move_to_warehouse(request, deal_id):
    """Move a deal to IN_WAREHOUSE status."""
    deal = get_object_or_404(Deal, id=deal_id)
    
    if request.method == 'POST':
        if not deal.vendor_invoice:
            messages.error(request, 'Vendor invoice is required before moving to warehouse.')
            return redirect('procurement')
        
        deal.status = 'IN_WAREHOUSE'
        deal.save()
        messages.success(request, f'Deal "{deal.item_name}" moved to warehouse!')
    
    return redirect('logistics')


def mark_shipped(request, deal_id):
    """Mark a deal as shipped."""
    deal = get_object_or_404(Deal, id=deal_id)
    
    if request.method == 'POST':
        tracking_id = request.POST.get('tracking_id', '')
        courier_partner = request.POST.get('courier_partner', '')
        
        if not tracking_id:
            messages.error(request, 'Tracking ID is required to mark as shipped.')
            return redirect('logistics')
        
        deal.tracking_id = tracking_id
        deal.courier_partner = courier_partner
        deal.status = 'SHIPPED'
        deal.save()
        messages.success(request, f'Deal "{deal.item_name}" marked as shipped!')
    
    return redirect('logistics')
