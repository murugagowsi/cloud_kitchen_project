from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('kitchen.urls')),
    path('api/invoices/', include('invoices.urls')),  # Phase 7 - NEW
    path('api/payments/', include('payments.urls')),
    path('api-auth/', include('rest_framework.urls')),
]