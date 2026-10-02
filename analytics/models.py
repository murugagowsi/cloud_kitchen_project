from django.db import models

class SalesReport(models.Model):
    date = models.DateField(auto_now_add=True)
    total_orders = models.IntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_customers = models.IntegerField(default=0)
    
    def __str__(self):
        return f"Sales Report - {self.date}"