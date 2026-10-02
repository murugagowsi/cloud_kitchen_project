from rest_framework import serializers
from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):

    PAYMENT_METHODS = [
        'credit_card',
        'debit_card',
        'upi',
        'wallet',
        'cash',
        'bank_transfer',
    ]

    class Meta:
        model = Payment
        fields = [
            'id',
            'order',
            'amount',
            'payment_method',
            'status',
            'transaction_id',
            'created_at'
        ]

    def validate_payment_method(self, value):
        if value not in self.PAYMENT_METHODS:
            raise serializers.ValidationError(
                "Invalid payment method. Choose: credit_card, debit_card, upi, wallet, cash, or bank_transfer."
            )
        return value