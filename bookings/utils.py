import uuid
from datetime import timedelta
from django.db import transaction
from django.db.models import Q, Count
from .models import Users, Teams, Rooms, RoomType, Bookings, BookingAttendees

class BookingError(Exception):
    pass

ONE_HOUR = timedelta(hours=1)

@transaction.atomic
def book_slot(slot_start, room_type, users=None, team: Teams | None = None):
    slot_end = slot_start + ONE_HOUR
    if users is None:
        users = []
    team_members = list(team.members.all()) if team else []
    attendees = users or team_members

    if room_type == RoomType.CONFERENCE and len(attendees) < 3:
        raise BookingError("Conference room bookings require at least 3.")
    
    #  Check attendees not already booked in this time slot
    overlapping_qs = BookingAttendees.objects.filter(
        booking__slot_start=slot_start,
        user__in=attendees,
    )
    if overlapping_qs.exists():
        raise BookingError("One or more users already have a booking in this slot.")
    
    def create_booking_on_room(room: Rooms, attendees_list, team=None):
        booking = Bookings.objects.create(
            room=room,
            team=team,
            slot_start=slot_start,
            slot_end=slot_end,
            booking_code = uuid.uuid4().hex[:12],
        )

        for user in attendees_list:
            BookingAttendees.objects.create(booking=booking, user=user)
        return booking
    
    # Private room booking
    if room_type == RoomType.PRIVATE:
        if not len(attendees) == 1:
            raise BookingError("Private room bookings are for single users only.")
        
        occupied_rooms_id = Bookings.objects.filter(
            slot_start=slot_start,
            room__room_type=RoomType.PRIVATE
        ).values_list('room_id', flat=True)

        room = Rooms.objects.select_for_update().filter(
            room_type=RoomType.PRIVATE
        ).exclude(
            id__in=occupied_rooms_id
        ).order_by('id').first()

        if not room:
            raise BookingError("No private rooms available for this slot.")
        return create_booking_on_room(room, attendees)
    
    # Conference room booking
    if room_type == RoomType.CONFERENCE:
        occupied_rooms_id = Bookings.objects.filter(
            slot_start=slot_start,
            room__room_type=RoomType.CONFERENCE
        ).values_list('room_id', flat=True)

        room = Rooms.objects.select_for_update().filter(
            room_type=RoomType.CONFERENCE,
        ).exclude(
            id__in=occupied_rooms_id
        ).order_by('id').first()

        if not room:
            raise BookingError("No conference rooms available for this slot")
        
        return create_booking_on_room(room, attendees, team=team)
    
    # Shared desk booking
    if room_type == RoomType.SHARED:
        if not len(attendees) == 1:
            raise BookingError("Shared desk booking accepts exactly one user per request.")
        
        user = attendees[0]
        shared_rooms = Rooms.objects.filter(room_type=RoomType.SHARED)

        existing = Bookings.objects.select_for_update().filter(
            slot_start=slot_start, room__in=shared_rooms
        ).annotate(seat_count=Count('attendees', filter=~Q(attendees__user__age__lt=10))).order_by('room_id')

        for booking in existing:
            if booking.seat_count < booking.room.capacity:
                BookingAttendees.objects.create(booking=booking, user=user)
                return booking
            
        occupied_rooms_id = set(existing.values_list('room_id', flat=True))
        room = Rooms.objects.select_for_update().filter(
            room_type=RoomType.SHARED,
        ).exclude(
            id__in=occupied_rooms_id
        ).order_by('id').first()
        if not room:
            raise BookingError("No shared rooms available for this slot.")
        return create_booking_on_room(room, [user]) # function expects a list of users and here user is attendees[0]
    
    raise BookingError("Invalid room type.")

@transaction.atomic
def cancel_booking(booking_code: str, user: Users | None = None):
    """
    Cancels a booking using its unique booking_code.
    """
    try:
        booking = Bookings.objects.select_for_update().get(booking_code=booking_code)
    except Bookings.DoesNotExist:
        raise BookingError("Booking Code not found.")
    
    # Cancel entire booking if no user specified
    if user is None:
        booking.delete()
        return
    # Cancel booking for specific user (Shared Desk scenario)
    deleted, _ = booking.attendees.filter(user=user).delete()

    if deleted == 0:
        raise BookingError("User not found in this booking.")
    
    if booking.attendees.count() == 0:
        booking.delete()
    