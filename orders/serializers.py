from rest_framework import serializers
from .models import Order, OrderItem, OrderTimeline

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['id', 'item_name', 'quantity', 'price', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

class OrderTimelineSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderTimeline
        fields = ['id', 'status', 'timestamp', 'notes']
        read_only_fields = ['id', 'timestamp']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    timeline = OrderTimelineSerializer(many=True, read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'customer_name', 'customer_phone', 'customer_email',
            'delivery_address', 'status', 'total_amount', 'special_notes',
            'created_at', 'updated_at', 'estimated_delivery', 'delivered_at',
            'items', 'timeline'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'items', 'timeline']

class OrderStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['status']