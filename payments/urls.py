from django.urls import path
from .views import create_payment, get_all_payments, get_payment_detail, get_order_payments

urlpatterns = [
    path('api/payments/', create_payment),
    path('api/payments/list/', get_all_payments),
    path('api/payments/<int:pk>/', get_payment_detail),
    path('api/orders/<int:order_id>/payments/', get_order_payments),
]

