from django.db import models

class Delivery(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    
    order_id = models.IntegerField(default=0)
    delivery_person = models.CharField(max_length=100)
    delivery_location = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    estimated_delivery_time = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Delivery {self.id} - {self.status}"