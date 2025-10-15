from django.test import TestCase
from django.utils import timezone
from .models import Users, Teams, Rooms, Bookings, BookingAttendees, RoomType
from datetime import datetime


class BaseTestSetup(TestCase):
    def setUp(self):
        # Create test users
        self.user1 = Users.objects.create(name="User One", age=25, gender='M')
        self.user2 = Users.objects.create(name="User Two", age=30, gender='F') 
        self.user3 = Users.objects.create(name="User Three", age=35, gender='M')
        self.child_user = Users.objects.create(name="Child User", age=8, gender='M')
        
        # Create team
        self.team = Teams.objects.create(name="Test Team")
        self.team.members.add(self.user1, self.user2, self.user3)
        
        # Create rooms
        self.private_room = Rooms.objects.create(
            room_number="P01", room_type=RoomType.PRIVATE, capacity=1
        )
        self.conference_room = Rooms.objects.create(
            room_number="C01", room_type=RoomType.CONFERENCE, capacity=10
        )
        self.shared_room = Rooms.objects.create(
            room_number="S01", room_type=RoomType.SHARED, capacity=4
        )
        
        # Test time slot
        # Test time slot - ensure it's on the hour and within working hours
        now = timezone.now()
        self.test_slot = timezone.make_aware(
            datetime(now.year, now.month, now.day, 10, 0, 0)  # 10:00 AM exactly
        )


class RoomBookingTests(BaseTestSetup):
    def test_private_room_booking_success(self):
        """Test successful private room booking for single user"""
        from .utils import book_slot
        
        booking = book_slot(
            slot_start=self.test_slot,
            room_type=RoomType.PRIVATE,
            users=[self.user1]
        )
        
        self.assertEqual(booking.room.room_type, RoomType.PRIVATE)
        self.assertEqual(booking.attendees.count(), 1)
        self.assertEqual(booking.attendees.first().user, self.user1)

    def test_private_room_booking_failure_multiple_users(self):
        """Test private room booking fails with multiple users"""
        from .utils import book_slot
        from .utils import BookingError
        
        with self.assertRaises(BookingError) as context:
            book_slot(
                slot_start=self.test_slot,
                room_type=RoomType.PRIVATE,
                users=[self.user1, self.user2]
            )
        
        self.assertIn("single users only", str(context.exception))

    def test_conference_room_booking_with_team(self):
        """Test conference room booking with valid team"""
        from .utils import book_slot
        
        booking = book_slot(
            slot_start=self.test_slot,
            room_type=RoomType.CONFERENCE,
            team=self.team
        )
        
        self.assertEqual(booking.room.room_type, RoomType.CONFERENCE)
        self.assertEqual(booking.attendees.count(), 3)

    def test_conference_room_booking_insufficient_members(self):
        """Test conference room booking fails with less than 3 members"""
        from .utils import book_slot, BookingError
        
        small_team = Teams.objects.create(name="Small Team")
        small_team.members.add(self.user1, self.user2)
        
        with self.assertRaises(BookingError) as context:
            book_slot(
                slot_start=self.test_slot,
                room_type=RoomType.CONFERENCE,
                team=small_team
            )
        
        self.assertIn("require at least 3", str(context.exception))

    def test_shared_desk_booking_single_user(self):
        """Test shared desk booking for single user"""
        from .utils import book_slot
        
        booking = book_slot(
            slot_start=self.test_slot,
            room_type=RoomType.SHARED,
            users=[self.user1]
        )
        
        self.assertEqual(booking.room.room_type, RoomType.SHARED)
        self.assertEqual(booking.attendees.count(), 1)

    def test_shared_desk_multiple_users_same_desk(self):
        """Test multiple users can book same shared desk"""
        from .utils import book_slot
        
        # First user
        booking1 = book_slot(
            slot_start=self.test_slot,
            room_type=RoomType.SHARED,
            users=[self.user1]
        )
        
        # Second user should join same desk
        booking2 = book_slot(
            slot_start=self.test_slot,
            room_type=RoomType.SHARED,
            users=[self.user2]
        )
        
        self.assertEqual(booking1.id, booking2.id)
        self.assertEqual(booking1.attendees.count(), 2)


class CancellationTests(BaseTestSetup):
    def test_full_booking_cancellation(self):
        """Test complete booking cancellation"""
        from .utils import book_slot, cancel_booking
        
        booking = book_slot(
            slot_start=self.test_slot,
            room_type=RoomType.PRIVATE,
            users=[self.user1]
        )
        
        booking_code = booking.booking_code
        cancel_booking(booking_code)
        
        # Verify booking is deleted
        self.assertFalse(Bookings.objects.filter(booking_code=booking_code).exists())

    def test_shared_desk_partial_cancellation(self):
        """Test partial cancellation for shared desk"""
        from .utils import book_slot, cancel_booking
        
        # Create shared desk with multiple users
        booking = book_slot(
            slot_start=self.test_slot,
            room_type=RoomType.SHARED,
            users=[self.user1]
        )
        # Add second user
        BookingAttendees.objects.create(booking=booking, user=self.user2)
        
        initial_count = booking.attendees.count()
        
        # Cancel only one user
        cancel_booking(booking.booking_code, user=self.user1)
        
        # Verify partial cancellation
        booking.refresh_from_db()
        self.assertEqual(booking.attendees.count(), initial_count - 1)
        self.assertTrue(Bookings.objects.filter(booking_code=booking.booking_code).exists())


