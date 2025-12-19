from django import forms
from django.utils import timezone
from .models import Partner, Transaction, Deal


class PartnerForm(forms.ModelForm):
    """Form for creating and updating Partners."""
    
    class Meta:
        model = Partner
        fields = ['name', 'gst_number', 'contact_info']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Partner Name'}),
            'gst_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'GST Number'}),
            'contact_info': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Contact Information'}),
        }


class TransactionForm(forms.ModelForm):
    """Form for creating Transactions (Advances/Refunds)."""
    
    class Meta:
        model = Transaction
        fields = ['partner', 'amount', 'transaction_type', 'date', 'evidence_file', 'notes']
        widgets = {
            'partner': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Amount'}),
            'transaction_type': forms.Select(attrs={'class': 'form-select'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'evidence_file': forms.FileInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Notes (optional)'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.initial.get('date'):
            self.initial['date'] = timezone.now().date()


class DealForm(forms.ModelForm):
    """Form for creating new Deals."""
    
    class Meta:
        model = Deal
        fields = [
            'partner', 'item_name', 'quantity', 
            'estimated_cost', 'actual_cost', 'commission_percent',
            'vendor_invoice', 'client_name', 'tracking_id', 'courier_partner', 'status'
        ]
        widgets = {
            'partner': forms.Select(attrs={'class': 'form-select'}),
            'item_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Item Name'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'estimated_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Estimated Cost'}),
            'actual_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Actual Cost'}),
            'commission_percent': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Commission %'}),
            'vendor_invoice': forms.FileInput(attrs={'class': 'form-control'}),
            'client_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'End Client Name'}),
            'tracking_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tracking ID'}),
            'courier_partner': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Courier Partner'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }


class QuickAdvanceForm(forms.ModelForm):
    """Simplified form for quick advance entry from dashboard."""
    
    class Meta:
        model = Transaction
        fields = ['partner', 'amount', 'date', 'evidence_file']
        widgets = {
            'partner': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Amount'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'evidence_file': forms.FileInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.initial.get('date'):
            self.initial['date'] = timezone.now().date()
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.transaction_type = 'ADVANCE_RECEIVED'
        if commit:
            instance.save()
        return instance


class DealStatusUpdateForm(forms.ModelForm):
    """Form for updating deal status and logistics info."""
    
    class Meta:
        model = Deal
        fields = ['actual_cost', 'vendor_invoice', 'tracking_id', 'courier_partner', 'status']
        widgets = {
            'actual_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'vendor_invoice': forms.FileInput(attrs={'class': 'form-control'}),
            'tracking_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tracking ID'}),
            'courier_partner': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Courier Partner'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }
