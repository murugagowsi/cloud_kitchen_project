from django.db import models
from django.utils import timezone
from orders.models import Order

class Payment(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=50)
    status = models.CharField(max_length=50)
    transaction_id = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(default=timezone.now)
    def __str__(self):
        return f"Payment {self.id} - Order {self.order_id}"