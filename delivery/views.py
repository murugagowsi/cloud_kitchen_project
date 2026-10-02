from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Delivery
from .serializers import DeliverySerializer


class DeliveryViewSet(viewsets.ModelViewSet):
    queryset = Delivery.objects.all()
    serializer_class = DeliverySerializer

    @action(detail=True, methods=['post'])
    def mark_delivered(self, request, pk=None):
        delivery = self.get_object()
        delivery.status = 'delivered'
        delivery.save()
        return Response({
            'message': 'Delivery marked as delivered',
            'status': delivery.status
        })

    @action(detail=True, methods=['post'])
    def start_delivery(self, request, pk=None):
        delivery = self.get_object()
        delivery.status = 'out_for_delivery'
        delivery.save()
        return Response({
            'message': 'Delivery started',
            'status': delivery.status
        })