from django.db import models
from orders.models import Order

class KitchenOrder(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('preparing', 'Preparing'),
        ('ready', 'Ready'),
    ]
    
    order = models.OneToOneField(Order, on_delete=models.CASCADE, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    started_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    special_instructions = models.TextField(blank=True)
    
    def __str__(self):
        if self.order and hasattr(self.order, 'order_number'):
            return f"Kitchen Order for #{self.order.order_number}"
        return f"Kitchen Order #{self.pk or 'New'}"


class Menu(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=100)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Menu {self.id} - {self.name}"