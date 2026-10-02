from django.db import models
from menu.models import FoodItem

class Inventory(models.Model):
    food_item = models.OneToOneField(FoodItem, on_delete=models.CASCADE)
    quantity_in_stock = models.IntegerField()
    reorder_level = models.IntegerField(help_text="Alert when stock goes below this")
    last_updated = models.DateTimeField(auto_now=True)
    
    def is_low_stock(self):
        return self.quantity_in_stock < self.reorder_level
    
    def __str__(self):
        return f"{self.food_item.name} - {self.quantity_in_stock} units"