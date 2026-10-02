from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import KitchenOrderViewSet, UserViewSet, MenuViewSet

router = DefaultRouter()
router.register(r'kitchen-orders', KitchenOrderViewSet)
router.register(r'users', UserViewSet, basename='user')
router.register(r'menus', MenuViewSet)

urlpatterns = [
    path('', include(router.urls)),
]