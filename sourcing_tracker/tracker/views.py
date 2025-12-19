from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum
from django.http import HttpResponse
from decimal import Decimal
from .models import Partner, Transaction, Deal, DealItem
from .forms import (
    PartnerForm, TransactionForm, DealForm, 
    QuickAdvanceForm, DealStatusUpdateForm, DealItemFormSet
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


def edit_partner(request, partner_id):
    """View for editing a partner."""
    partner = get_object_or_404(Partner, id=partner_id)
    
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        gst_number = request.POST.get('gst_number', '').strip()
        contact_info = request.POST.get('contact_info', '').strip()
        
        if not name or not gst_number:
            messages.error(request, 'Name and GST Number are required.')
            return redirect('dashboard')
        
        # Check if GST number is being changed and if it's already in use
        if gst_number != partner.gst_number:
            if Partner.objects.filter(gst_number=gst_number).exists():
                messages.error(request, f'GST Number {gst_number} is already in use by another partner.')
                return redirect('dashboard')
        
        partner.name = name
        partner.gst_number = gst_number
        partner.contact_info = contact_info
        partner.save()
        
        messages.success(request, f'Partner "{partner.name}" updated successfully!')
    
    return redirect('dashboard')


def delete_partner(request, partner_id):
    """View for deleting a partner."""
    partner = get_object_or_404(Partner, id=partner_id)
    
    if request.method == 'POST':
        # Check if partner has any transactions or deals
        has_transactions = partner.transactions.exists()
        has_deals = partner.deals.exists()
        
        if has_transactions or has_deals:
            messages.error(
                request, 
                f'Cannot delete "{partner.name}" because they have existing transactions or deals. '
                'Please delete those first.'
            )
            return redirect('dashboard')
        
        partner_name = partner.name
        partner.delete()
        messages.success(request, f'Partner "{partner_name}" deleted successfully!')
    
    return redirect('dashboard')


def ledger(request):
    """
    Ledger view showing all transactions with filtering by partner and date.
    """
    from datetime import datetime, timedelta
    from django.utils import timezone
    
    transactions = Transaction.objects.select_related('partner').all()
    partners = Partner.objects.all()
    
    # Filter by partner if specified
    partner_id = request.GET.get('partner')
    if partner_id:
        transactions = transactions.filter(partner_id=partner_id)
    
    # Date filtering
    date_filter = request.GET.get('date_filter', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    
    today = timezone.now().date()
    
    if date_filter == 'this_month':
        first_day = today.replace(day=1)
        transactions = transactions.filter(date__gte=first_day, date__lte=today)
        start_date = first_day.strftime('%Y-%m-%d')
        end_date = today.strftime('%Y-%m-%d')
    elif date_filter == 'last_month':
        first_day_this_month = today.replace(day=1)
        last_day_last_month = first_day_this_month - timedelta(days=1)
        first_day_last_month = last_day_last_month.replace(day=1)
        transactions = transactions.filter(date__gte=first_day_last_month, date__lte=last_day_last_month)
        start_date = first_day_last_month.strftime('%Y-%m-%d')
        end_date = last_day_last_month.strftime('%Y-%m-%d')
    elif date_filter == 'last_3_months':
        three_months_ago = today - timedelta(days=90)
        transactions = transactions.filter(date__gte=three_months_ago, date__lte=today)
        start_date = three_months_ago.strftime('%Y-%m-%d')
        end_date = today.strftime('%Y-%m-%d')
    elif date_filter == 'custom' and start_date and end_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
            transactions = transactions.filter(date__gte=start, date__lte=end)
        except ValueError:
            pass
    
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
        'date_filter': date_filter,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'tracker/ledger.html', context)


def export_ledger_csv(request):
    """Export ledger transactions to CSV with applied filters."""
    import csv
    from datetime import datetime, timedelta
    from django.utils import timezone
    from django.http import HttpResponse
    
    transactions = Transaction.objects.select_related('partner').all()
    
    # Apply same filters as ledger view
    partner_id = request.GET.get('partner')
    if partner_id:
        transactions = transactions.filter(partner_id=partner_id)
    
    date_filter = request.GET.get('date_filter', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    
    today = timezone.now().date()
    
    if date_filter == 'this_month':
        first_day = today.replace(day=1)
        transactions = transactions.filter(date__gte=first_day, date__lte=today)
        start_date = first_day.strftime('%Y-%m-%d')
        end_date = today.strftime('%Y-%m-%d')
    elif date_filter == 'last_month':
        first_day_this_month = today.replace(day=1)
        last_day_last_month = first_day_this_month - timedelta(days=1)
        first_day_last_month = last_day_last_month.replace(day=1)
        transactions = transactions.filter(date__gte=first_day_last_month, date__lte=last_day_last_month)
        start_date = first_day_last_month.strftime('%Y-%m-%d')
        end_date = last_day_last_month.strftime('%Y-%m-%d')
    elif date_filter == 'last_3_months':
        three_months_ago = today - timedelta(days=90)
        transactions = transactions.filter(date__gte=three_months_ago, date__lte=today)
        start_date = three_months_ago.strftime('%Y-%m-%d')
        end_date = today.strftime('%Y-%m-%d')
    elif date_filter == 'custom' and start_date and end_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
            transactions = transactions.filter(date__gte=start, date__lte=end)
        except ValueError:
            pass
    
    # Create CSV response
    filename = f"ledger_export_{today.strftime('%Y%m%d')}"
    if start_date and end_date:
        filename = f"ledger_{start_date}_to_{end_date}"
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Date', 'Partner', 'GST Number', 'Transaction Type', 'Amount', 'Notes'])
    
    for txn in transactions:
        writer.writerow([
            txn.date.strftime('%Y-%m-%d'),
            txn.partner.name,
            txn.partner.gst_number,
            txn.get_transaction_type_display(),
            f"{'+' if txn.transaction_type == 'ADVANCE_RECEIVED' else '-'}{txn.amount}",
            txn.notes or '',
        ])
    
    return response


def edit_transaction(request, transaction_id):
    """View for editing an existing transaction."""
    transaction = get_object_or_404(Transaction, id=transaction_id)
    old_amount = transaction.amount
    old_type = transaction.transaction_type
    
    if request.method == 'POST':
        # Get the new values from the form
        new_amount = request.POST.get('amount')
        new_type = request.POST.get('transaction_type')
        new_date = request.POST.get('date')
        new_notes = request.POST.get('notes', '')
        
        try:
            new_amount = Decimal(new_amount)
        except:
            messages.error(request, 'Invalid amount.')
            return redirect('ledger')
        
        # Reverse the old transaction effect on partner balance
        partner = transaction.partner
        if old_type == 'ADVANCE_RECEIVED':
            partner.current_balance -= old_amount
        else:  # REFUND_GIVEN
            partner.current_balance += old_amount
        
        # Apply the new transaction effect
        if new_type == 'ADVANCE_RECEIVED':
            partner.current_balance += new_amount
        else:  # REFUND_GIVEN
            partner.current_balance -= new_amount
        
        partner.save()
        
        # Update the transaction
        transaction.amount = new_amount
        transaction.transaction_type = new_type
        transaction.date = new_date
        transaction.notes = new_notes
        
        # Handle file upload
        if 'evidence_file' in request.FILES:
            transaction.evidence_file = request.FILES['evidence_file']
        
        transaction.save()
        messages.success(request, 'Transaction updated successfully!')
        
    return redirect('ledger')


def delete_transaction(request, transaction_id):
    """View for deleting a transaction."""
    transaction = get_object_or_404(Transaction, id=transaction_id)
    
    if request.method == 'POST':
        # Reverse the transaction effect on partner balance
        partner = transaction.partner
        if transaction.transaction_type == 'ADVANCE_RECEIVED':
            partner.current_balance -= transaction.amount
        else:  # REFUND_GIVEN
            partner.current_balance += transaction.amount
        
        partner.save()
        
        item_description = f"{transaction.get_transaction_type_display()} - ₹{transaction.amount}"
        transaction.delete()
        messages.success(request, f'Transaction "{item_description}" deleted successfully!')
    
    return redirect('ledger')


def procurement(request):
    """
    Procurement view showing active deals (SOURCING and BOOKED status).
    """
    active_deals = Deal.objects.filter(
        status__in=['SOURCING', 'BOOKED']
    ).select_related('partner').prefetch_related('items')
    
    partners = Partner.objects.all()
    
    if request.method == 'POST':
        form = DealForm(request.POST, request.FILES)
        formset = DealItemFormSet(request.POST, prefix='items')
        
        if form.is_valid() and formset.is_valid():
            # Save the deal first
            deal = form.save()
            
            # Save the items linked to the deal
            items = formset.save(commit=False)
            for item in items:
                item.deal = deal
                item.save()
            
            # Handle deleted items (if any)
            for obj in formset.deleted_objects:
                obj.delete()
            
            messages.success(request, f'Deal "{deal.reference}" created successfully!')
            return redirect('procurement')
        else:
            messages.error(request, 'Error creating deal. Please check the form.')
    else:
        form = DealForm()
        formset = DealItemFormSet(prefix='items', queryset=DealItem.objects.none())
        # Default to SOURCING status for new deals
        form.initial['status'] = 'SOURCING'
    
    context = {
        'deals': active_deals,
        'partners': partners,
        'form': form,
        'formset': formset,
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


def delete_deal(request, deal_id):
    """View for deleting a deal."""
    deal = get_object_or_404(Deal, id=deal_id)
    
    if request.method == 'POST':
        deal_reference = deal.reference
        # Delete all associated items first (cascade should handle this, but being explicit)
        deal.items.all().delete()
        deal.delete()
        messages.success(request, f'Deal "{deal_reference}" deleted successfully!')
    
    return redirect('procurement')


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
