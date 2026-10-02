from django.urls import path
from .views import create_payment, get_all_payments, get_payment_detail, get_order_payments

urlpatterns = [
    path('', create_payment),
    path('list/', get_all_payments),
    path('<int:pk>/', get_payment_detail),
    path('order/<int:order_id>/', get_order_payments),
   ]