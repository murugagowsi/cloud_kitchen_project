from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import InvoiceViewSet

# Create router and register ViewSet
router = DefaultRouter()
router.register(r'', InvoiceViewSet, basename='invoice')

# URL patterns
urlpatterns = [
    path('', include(router.urls)),
]