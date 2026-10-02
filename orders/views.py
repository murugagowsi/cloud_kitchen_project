from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from .models import Order, OrderItem, OrderTimeline
from .serializers import (
    OrderSerializer,
    OrderStatusUpdateSerializer,
    OrderItemSerializer,
    OrderTimelineSerializer
)


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    filterset_fields = ['status', 'customer_name']
    search_fields = ['order_number', 'customer_name', 'customer_phone']
    ordering_fields = ['created_at', 'total_amount']
    ordering = ['-created_at']
    
    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        """Update order status and create timeline entry"""
        order = self.get_object()
        serializer = OrderStatusUpdateSerializer(data=request.data)
        
        if serializer.is_valid():
            new_status = serializer.validated_data['status']
            
            # Validate status transition
            valid_transitions = {
                'pending': ['confirmed', 'cancelled'],
                'confirmed': ['preparing', 'cancelled'],
                'preparing': ['ready', 'cancelled'],
                'ready': ['out_for_delivery', 'cancelled'],
                'out_for_delivery': ['delivered', 'cancelled'],
                'delivered': [],
                'cancelled': [],
            }
            
            if new_status not in valid_transitions.get(order.status, []):
                return Response(
                    {'error': f'Cannot transition from {order.status} to {new_status}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Update order status
            order.status = new_status
            if new_status == 'delivered':
                order.delivered_at = timezone.now()
            order.save()
            
            # Create timeline entry
            OrderTimeline.objects.create(
                order=order,
                status=new_status,
                notes=request.data.get('notes', '')
            )
            
            return Response(self.get_serializer(order).data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Get all pending orders"""
        pending_orders = Order.objects.filter(status='pending')
        serializer = self.get_serializer(pending_orders, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def in_progress(self, request):
        """Get all orders in progress (confirmed, preparing, ready, out_for_delivery)"""
        in_progress_orders = Order.objects.filter(
            status__in=['confirmed', 'preparing', 'ready', 'out_for_delivery']
        )
        serializer = self.get_serializer(in_progress_orders, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def completed(self, request):
        """Get all completed orders"""
        completed_orders = Order.objects.filter(status='delivered')
        serializer = self.get_serializer(completed_orders, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def cancelled(self, request):
        """Get all cancelled orders"""
        cancelled_orders = Order.objects.filter(status='cancelled')
        serializer = self.get_serializer(cancelled_orders, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def timeline(self, request, pk=None):
        """Get full timeline for an order"""
        order = self.get_object()
        timeline = order.timeline.all()
        serializer = OrderTimelineSerializer(timeline, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_items(self, request, pk=None):
        """Add items to an order"""
        order = self.get_object()
        items_data = request.data.get('items', [])
        
        created_items = []
        for item_data in items_data:
            item = OrderItem.objects.create(
                order=order,
                item_name=item_data.get('item_name'),
                quantity=item_data.get('quantity', 1),
                price=item_data.get('price')
            )
            created_items.append(item)
        
        # Update total amount
        order.total_amount = sum(item.price * item.quantity for item in order.items.all())
        order.save()
        
        return Response(self.get_serializer(order).data)
    
    @action(detail=True, methods=['delete'])
    def cancel(self, request, pk=None):
        """Cancel an order"""
        order = self.get_object()
        
        if order.status in ['delivered', 'cancelled']:
            return Response(
                {'error': f'Cannot cancel order with status: {order.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        order.status = 'cancelled'
        order.save()
        
        # Create timeline entry
        OrderTimeline.objects.create(
            order=order,
            status='cancelled',
            notes=request.data.get('reason', 'Cancelled by user')
        )
        
        return Response({'message': 'Order cancelled successfully'})
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get order statistics"""
        total_orders = Order.objects.count()
        pending = Order.objects.filter(status='pending').count()
        in_progress = Order.objects.filter(status__in=['confirmed', 'preparing', 'ready', 'out_for_delivery']).count()
        delivered = Order.objects.filter(status='delivered').count()
        cancelled = Order.objects.filter(status='cancelled').count()
        
        return Response({
            'total_orders': total_orders,
            'pending': pending,
            'in_progress': in_progress,
            'delivered': delivered,
            'cancelled': cancelled,
        })