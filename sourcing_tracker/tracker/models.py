from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from simple_history.models import HistoricalRecords


class Partner(models.Model):
    """Model representing a partner company (e.g., Company X, Company Y)."""
    
    name = models.CharField(max_length=200)
    gst_number = models.CharField(max_length=15, unique=True, verbose_name="GST Number")
    contact_info = models.TextField(blank=True, verbose_name="Contact Information")
    current_balance = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=Decimal('0.00'),
        verbose_name="Current Balance"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    history = HistoricalRecords()
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.gst_number})"


class Transaction(models.Model):
    """Model representing money movements (advances received or refunds given)."""
    
    TRANSACTION_TYPES = [
        ('ADVANCE_RECEIVED', 'Advance Received'),
        ('REFUND_GIVEN', 'Refund Given'),
    ]
    
    partner = models.ForeignKey(
        Partner, 
        on_delete=models.CASCADE, 
        related_name='transactions'
    )
    amount = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    transaction_type = models.CharField(
        max_length=20, 
        choices=TRANSACTION_TYPES,
        verbose_name="Transaction Type"
    )
    date = models.DateField()
    evidence_file = models.FileField(
        upload_to='transaction_evidence/', 
        blank=True, 
        null=True,
        verbose_name="Evidence (Bank Screenshot)"
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    history = HistoricalRecords()
    
    class Meta:
        ordering = ['-date', '-created_at']
    
    def __str__(self):
        return f"{self.partner.name} - {self.get_transaction_type_display()} - ₹{self.amount}"


import uuid
from django.utils import timezone as tz

def generate_reference():
    """Generate a unique reference number for deals."""
    date_str = tz.now().strftime('%Y%m%d')
    return f"DEAL-{date_str}-{uuid.uuid4().hex[:4].upper()}"


class Deal(models.Model):
    """Model representing a procurement deal/order."""
    
    STATUS_CHOICES = [
        ('SOURCING', 'Sourcing'),
        ('BOOKED', 'Booked'),
        ('IN_WAREHOUSE', 'In Warehouse'),
        ('SHIPPED', 'Shipped'),
        ('DELIVERED', 'Delivered'),
        ('RETURNED', 'Returned'),
    ]
    
    # Auto-generated reference number
    reference = models.CharField(
        max_length=20, 
        unique=True, 
        default=generate_reference,
        editable=False,
        verbose_name="Reference"
    )
    
    partner = models.ForeignKey(
        Partner, 
        on_delete=models.CASCADE, 
        related_name='deals'
    )
    
    # Legacy fields - kept for backward compatibility with existing deals
    item_name = models.CharField(max_length=300, verbose_name="Item Name", blank=True)
    quantity = models.PositiveIntegerField(default=1)
    
    # Financials (legacy - now calculated from DealItems)
    estimated_cost = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        null=True, 
        blank=True,
        verbose_name="Estimated Cost"
    )
    actual_cost = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        null=True, 
        blank=True,
        verbose_name="Actual Cost"
    )
    commission_percent = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=Decimal('0.00'),
        verbose_name="Commission %"
    )
    
    # Logistics
    vendor_invoice = models.FileField(
        upload_to='vendor_invoices/', 
        blank=True, 
        null=True,
        verbose_name="Vendor Invoice"
    )
    client_name = models.CharField(
        max_length=200, 
        blank=True,
        verbose_name="End Client Name"
    )
    tracking_id = models.CharField(
        max_length=100, 
        blank=True,
        verbose_name="Tracking ID"
    )
    courier_partner = models.CharField(
        max_length=100, 
        blank=True,
        verbose_name="Courier Partner"
    )
    
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='SOURCING'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Track if actual_cost has been deducted from balance
    cost_deducted = models.BooleanField(default=False)
    
    history = HistoricalRecords()
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.reference} - {self.partner.name} ({self.get_status_display()})"
    
    @property
    def total_amount(self):
        """Calculate total amount from all deal items."""
        return sum(item.total for item in self.items.all())
    
    @property
    def total_commission(self):
        """Calculate total commission from all deal items."""
        return sum(item.commission_total for item in self.items.all())
    
    @property
    def total_quantity(self):
        """Calculate total quantity from all deal items."""
        return sum(item.quantity for item in self.items.all())
    
    @property
    def commission_amount(self):
        """Calculate the commission amount - uses new item-based calculation if items exist."""
        if self.items.exists():
            return self.total_commission
        # Legacy calculation for old deals
        if self.actual_cost and self.commission_percent:
            return (self.actual_cost * self.commission_percent) / 100
        return Decimal('0.00')
    
    @property
    def is_over_budget(self):
        """Check if actual cost exceeds estimated cost."""
        if self.actual_cost and self.estimated_cost:
            return self.actual_cost > self.estimated_cost
        return False


class DealItem(models.Model):
    """Model representing an individual item in a deal."""
    
    deal = models.ForeignKey(
        Deal,
        on_delete=models.CASCADE,
        related_name='items'
    )
    item_name = models.CharField(max_length=300, verbose_name="Item Name")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Quantity")
    item_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Item Price (per unit)"
    )
    commission_per_item = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Commission per Item"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    history = HistoricalRecords()
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.item_name} x{self.quantity}"
    
    @property
    def total(self):
        """Calculate total: quantity * item_price"""
        return self.item_price * self.quantity
    
    @property
    def commission_total(self):
        """Calculate total commission: commission_per_item * quantity"""
        return self.commission_per_item * self.quantity
