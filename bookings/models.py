from django.db import models
from django.utils import timezone

# Create your models here.
class Gender(models.TextChoices):
    MALE = 'M', 'Male'
    FEMALE = 'F', 'Female' 
    OTHER = 'O', 'Other'

class Users(models.Model):
    name = models.CharField(max_length=120)
    age = models.PositiveIntegerField()
    gender = models.CharField(max_length=1, choices=Gender.choices)

    def __str__(self):
        return f'{self.name} ({self.age})'
    
class Teams(models.Model):
    name = models.CharField(max_length=120)
    members = models.ManyToManyField(Users, related_name='teams')

    def __str__(self):
        return self.name
    
    def total_members_count(self):
        return self.members.count()
    
    def total_seats_counts(self):
        return self.members.exclude(age__lt=10).count()
    
class RoomType(models.TextChoices):
    PRIVATE = 'private', 'Private'
    CONFERENCE = 'conference', 'Conference'
    SHARED = 'shared', 'SharedDesk'

class Rooms(models.Model):
    room_number = models.CharField(max_length=10, unique=True)
    room_type = models.CharField(max_length=16, choices=RoomType.choices)
    capacity = models.PositiveIntegerField()

    def __str__(self):
        return f'Room {self.room_number} ({self.room_type})'
    
       
class Bookings(models.Model):
    room = models.ForeignKey(Rooms, on_delete=models.CASCADE, related_name='bookings')
    team = models.ForeignKey(Teams, on_delete=models.SET_NULL, null=True, blank=True)
    slot_start = models.DateTimeField()
    slot_end = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    booking_code = models.CharField(max_length=20, unique=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['room', 'slot_start'], name='unique_room_slot')
        ]

    def __str__(self):
        return f'Booking {self.booking_code} for Room {self.room.room_number} @ {self.slot_start:%Y-%m-%d %H:%M}'    
    
class BookingAttendees(models.Model):
    booking = models.ForeignKey(Bookings, on_delete=models.CASCADE, related_name='attendees')
    user = models.ForeignKey(Users, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['booking', 'user'], name='unique_booking_user')
        ]

    def __str__(self):
        return f'Attendee {self.user.name} for Booking {self.booking}'