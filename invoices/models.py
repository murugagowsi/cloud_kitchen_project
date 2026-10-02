from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
import uuid


class Invoice(models.Model):
    """
    Main invoice model - stores invoice data for each order
    """

    INVOICE_STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('issued', 'Issued'),
        ('paid', 'Paid'),
        ('partially_paid', 'Partially Paid'),
        ('refunded', 'Refunded'),
        ('cancelled', 'Cancelled'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('credit_card', 'Credit Card'),
        ('debit_card', 'Debit Card'),
        ('upi', 'UPI'),
        ('wallet', 'Wallet'),
        ('cash', 'Cash'),
        ('bank_transfer', 'Bank Transfer'),
    ]

    # Primary Identifiers
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice_number = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="Auto-generated invoice number (INV-YYYY-MM-00001)"
    )

    # Relationships
    order = models.OneToOneField(
    'orders.Order',     # ← CHANGE 'kitchen.Order' TO 'orders.Order'
    on_delete=models.PROTECT,
    related_name='invoice',
    help_text="Associated order"
)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    # Financial Data
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Order total before tax/discount"
    )
    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Discount applied"
    )
    tax_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="GST/Tax (default 5%)"
    )
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Final amount due (subtotal - discount + tax)"
    )
    amount_paid = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Amount received so far"
    )

    # Status & Tracking
    status = models.CharField(
        max_length=20,
        choices=INVOICE_STATUS_CHOICES,
        default='draft',
        db_index=True
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        null=True,
        blank=True
    )
    transaction_id = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True,
        db_index=True,
        help_text="Payment gateway transaction ID"
    )

    # Dates
    issued_date = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField(null=True, blank=True)
    paid_date = models.DateTimeField(null=True, blank=True)
    cancelled_date = models.DateTimeField(null=True, blank=True)

    # Notes & History
    notes = models.TextField(blank=True, help_text="Internal notes or refund reasons")
    payment_notes = models.TextField(blank=True, help_text="Customer-facing payment info")

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.CharField(
        max_length=100,
        default='system',
        help_text="Who/what created this invoice"
    )

    class Meta:
        ordering = ['-issued_date']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status', 'issued_date']),
            models.Index(fields=['order']),
        ]

    def __str__(self):
        return f"{self.invoice_number} - {self.user.get_full_name()} - {self.status}"

    @property
    def is_overdue(self):
        if self.due_date and not self.paid_date:
            return timezone.now() > self.due_date
        return False

    @property
    def remaining_amount(self):
        return self.total_amount - self.amount_paid

    def mark_as_paid(self, amount=None, transaction_id=None):
        """Update invoice as paid"""
        if amount is None:
            amount = self.total_amount
        
        self.amount_paid += amount
        
        if self.amount_paid >= self.total_amount:
            self.status = 'paid'
            self.paid_date = timezone.now()
        else:
            self.status = 'partially_paid'
        
        if transaction_id:
            self.transaction_id = transaction_id
        
        self.save()

    def mark_as_cancelled(self, reason=''):
        """Cancel invoice"""
        self.status = 'cancelled'
        self.cancelled_date = timezone.now()
        if reason:
            self.notes = f"Cancelled: {reason}"
        self.save()


class InvoiceItem(models.Model):
    """Line items in an invoice (denormalized from order items)"""
    
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='items'
    )
    
    item_name = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.item_name} x{self.quantity}"