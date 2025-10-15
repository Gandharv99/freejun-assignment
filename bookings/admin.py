from django.contrib import admin
from .models import Users, Teams, Rooms, Bookings, BookingAttendees

# Register your models here.
admin.site.register(Users)
admin.site.register(Teams)
admin.site.register(Rooms)
admin.site.register(Bookings)
admin.site.register(BookingAttendees)