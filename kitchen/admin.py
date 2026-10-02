from django.contrib import admin
from .models import KitchenOrder

@admin.register(KitchenOrder)
class KitchenOrderAdmin(admin.ModelAdmin):
    list_display = ['order', 'status', 'started_at', 'completed_at']
    list_filter = ['status']
    search_fields = ['order__order_number']