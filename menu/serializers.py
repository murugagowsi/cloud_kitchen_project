from rest_framework import serializers
from .models import Category, FoodItem

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class FoodItemSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = FoodItem
        fields = [
            'id', 'category', 'category_name', 'name', 'description',
            'price', 'discount_price', 'is_available', 'is_vegetarian',
            'portion_size', 'calories', 'preparation_time',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']