"""
Invoice API Serializers
File: invoices/serializers.py

Serializers convert Invoice & InvoiceItem models to JSON format
"""

from rest_framework import serializers
from .models import Invoice, InvoiceItem
from orders.models import Order
from django.contrib.auth.models import User


class InvoiceItemSerializer(serializers.ModelSerializer):
    """Serializer for invoice line items"""
    
    class Meta:
        model = InvoiceItem
        fields = [
            'id', 'item_name', 'quantity', 'unit_price',
            'total_price', 'notes'
        ]
        read_only_fields = ['id', 'total_price']


class InvoiceSerializer(serializers.ModelSerializer):
    """Full invoice serializer with all details"""
    
    items = InvoiceItemSerializer(many=True, read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    order_details = serializers.SerializerMethodField(read_only=True)
    remaining_amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True
    )
    is_overdue = serializers.BooleanField(read_only=True)

    class Meta:
        model = Invoice
        fields = [
            'id', 'invoice_number', 'order', 'order_details',
            'user', 'user_name', 'subtotal', 'discount_amount',
            'tax_amount', 'total_amount', 'amount_paid',
            'remaining_amount', 'status', 'payment_method',
            'transaction_id', 'issued_date', 'due_date',
            'paid_date', 'cancelled_date', 'notes',
            'payment_notes', 'items', 'is_overdue', 'created_at',
            'updated_at'
        ]
        read_only_fields = [
            'id', 'invoice_number', 'issued_date', 'created_at',
            'updated_at', 'paid_date', 'cancelled_date'
        ]

    def get_order_details(self, obj):
        """Get order information"""
        return {
            'id': obj.order.id,
            'order_number': getattr(obj.order, 'order_number', 'N/A'),
            'status': getattr(obj.order, 'status', 'N/A'),
            'created_at': obj.order.created_at,
        }


class InvoiceCreateSerializer(serializers.Serializer):
    """Serializer for creating invoice from an existing order"""
    
    order_id = serializers.IntegerField()
    due_date = serializers.DateTimeField(required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True)

    def validate_order_id(self, value):
        """Check if order exists and doesn't already have an invoice"""
        try:
            order = Order.objects.get(id=value)
            if hasattr(order, 'invoice'):
                raise serializers.ValidationError(
                    "An invoice already exists for this order."
                )
            return order
        except Order.DoesNotExist:
            raise serializers.ValidationError("Order not found.")


class InvoiceStatusUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating invoice status"""
    
    class Meta:
        model = Invoice
        fields = ['status', 'notes']

    def validate_status(self, value):
        """Validate status transitions are allowed"""
        if not self.instance:
            return value
            
        allowed_transitions = {
            'draft': ['issued', 'cancelled'],
            'issued': ['paid', 'partially_paid', 'cancelled'],
            'partially_paid': ['paid', 'refunded'],
            'paid': ['refunded'],
            'refunded': [],
            'cancelled': [],
        }
        current_status = self.instance.status
        
        if value not in allowed_transitions.get(current_status, []):
            raise serializers.ValidationError(
                f"Cannot transition from '{current_status}' to '{value}'"
            )
        return value


class InvoiceListSerializer(serializers.ModelSerializer):
    """Simplified serializer for list view (less data)"""
    
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    remaining_amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True
    )

    class Meta:
        model = Invoice
        fields = [
            'id', 'invoice_number', 'user', 'user_name',
            'total_amount', 'amount_paid', 'remaining_amount',
            'status', 'issued_date', 'due_date', 'payment_method'
        ]


class InvoicePaymentSerializer(serializers.Serializer):
    """Serializer for recording a payment"""
    
    amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        allow_null=True
    )
    transaction_id = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True
    )
    payment_method = serializers.ChoiceField(
        choices=Invoice.PAYMENT_METHOD_CHOICES,
        required=False
    )
    notes = serializers.CharField(
        required=False,
        allow_blank=True
    )

    def validate_amount(self, value):
        """Validate payment amount"""
        if value is not None and value <= 0:
            raise serializers.ValidationError("Amount must be positive.")
        return value


class InvoiceCancelSerializer(serializers.Serializer):
    """Serializer for cancelling an invoice"""
    
    reason = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Reason for cancellation"
    )