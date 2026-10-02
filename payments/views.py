from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Payment
from .serializers import PaymentSerializer


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_payment(request):
    serializer = PaymentSerializer(data=request.data)
    if serializer.is_valid():
        if serializer.validated_data['amount'] <= 0:
            return Response(
                {'error': 'Amount must be greater than 0.'},
                status=400
            )
        serializer.save()
        return Response(serializer.data, status=201)
    return Response(serializer.errors, status=400)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_payments(request):
    payments = Payment.objects.all()
    serializer = PaymentSerializer(payments, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_payment_detail(request, pk):
    try:
        payment = Payment.objects.get(pk=pk)
        serializer = PaymentSerializer(payment)
        return Response(serializer.data)
    except Payment.DoesNotExist:
        return Response({"error": "Payment not found"}, status=404)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_order_payments(request, order_id):
    payments = Payment.objects.filter(order_id=order_id)
    serializer = PaymentSerializer(payments, many=True)
    return Response(serializer.data)