from django.db import models
from django.contrib.auth.models import User
from menu.models import FoodItem

class Recommendation(models.Model):
    customer = models.ForeignKey(User, on_delete=models.CASCADE)
    food_item = models.ForeignKey(FoodItem, on_delete=models.CASCADE)
    score = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Recommendation: {self.food_item.name} for {self.customer.username}"