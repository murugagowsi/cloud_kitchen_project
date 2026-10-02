from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Category, FoodItem
from .serializers import CategorySerializer, FoodItemSerializer

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    
    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        category = self.get_object()
        category.is_active = not category.is_active
        category.save()
        return Response({
            'id': category.id,
            'name': category.name,
            'is_active': category.is_active
        })
    
    @action(detail=True, methods=['get'])
    def active_items(self, request, pk=None):
        category = self.get_object()
        items = category.fooditem_set.filter(is_active=True)
        serializer = FoodItemSerializer(items, many=True)
        return Response(serializer.data)


class FoodItemViewSet(viewsets.ModelViewSet):
    queryset = FoodItem.objects.all()
    serializer_class = FoodItemSerializer
    filterset_fields = ['category', 'is_available', 'is_vegetarian']
    search_fields = ['name', 'description']
    ordering_fields = ['price', 'preparation_time', 'created_at']
    
    @action(detail=False, methods=['get'])
    def available(self, request):
        items = FoodItem.objects.filter(is_available=True)
        serializer = self.get_serializer(items, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def unavailable(self, request):
        items = FoodItem.objects.filter(is_available=False)
        serializer = self.get_serializer(items, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def on_discount(self, request):
        items = FoodItem.objects.filter(discount_price__isnull=False).exclude(discount_price=0)
        serializer = self.get_serializer(items, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_dietary(self, request):
        is_veg = request.query_params.get('vegetarian', None)
        if is_veg:
            items = FoodItem.objects.filter(is_vegetarian=True)
        else:
            items = FoodItem.objects.filter(is_vegetarian=False)
        serializer = self.get_serializer(items, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def quick_items(self, request):
        max_time = request.query_params.get('max_time', 30)
        items = FoodItem.objects.filter(preparation_time__lte=max_time)
        serializer = self.get_serializer(items, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['patch'])
    def update_availability(self, request, pk=None):
        item = self.get_object()
        item.is_available = request.data.get('is_available', item.is_available)
        item.save()
        serializer = self.get_serializer(item)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        item = self.get_object()
        item.is_active = not item.is_active
        item.save()
        return Response({
            'id': item.id,
            'name': item.name,
            'is_active': item.is_active
        })