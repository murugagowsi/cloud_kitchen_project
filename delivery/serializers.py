from rest_framework import serializers
from .models import Delivery

class DeliverySerializer(serializers.ModelSerializer):
    class Meta:
        model = Delivery
        fields = ['id', 'order_id', 'delivery_person', 'delivery_location', 
                  'status', 'created_at', 'updated_at', 'estimated_delivery_time']