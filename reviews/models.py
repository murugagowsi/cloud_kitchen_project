from django.db import models
from django.contrib.auth.models import User
from orders.models import Order

class Review(models.Model):
    RATING_CHOICES = [
        (1, '1 - Poor'),
        (2, '2 - Fair'),
        (3, '3 - Good'),
        (4, '4 - Very Good'),
        (5, '5 - Excellent'),
    ]
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    customer = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=RATING_CHOICES)
    comment = models.TextField(blank=True)
    review_date = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Review for Order {self.order.order_number}"