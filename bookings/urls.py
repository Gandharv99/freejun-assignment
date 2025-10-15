from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, TeamViewSet, BookingViewSet, available_rooms

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'teams', TeamViewSet)
router.register(r'bookings', BookingViewSet, basename='booking')

urlpatterns = [
    path('rooms/available/', available_rooms, name='available-rooms'),
    path('', include(router.urls)),
    ]