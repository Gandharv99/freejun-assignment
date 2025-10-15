from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action, api_view
from rest_framework.exceptions import ValidationError
from django.utils.dateparse import parse_datetime
from django.db.models import Q, Count
from .models import Users, Teams, Rooms, Bookings, RoomType
from .serializers import UserSerializer, TeamSerializer, BookingSerializer, CreateBookingSerializer
from .utils import book_slot, cancel_booking, BookingError

# Create your views here.
class UserViewSet(viewsets.ModelViewSet):
    queryset = Users.objects.all()
    serializer_class = UserSerializer

class TeamViewSet(viewsets.ModelViewSet):
    queryset = Teams.objects.prefetch_related('members').all()
    serializer_class = TeamSerializer

class BookingViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Bookings.objects.select_related('room', 'team').prefetch_related('attendees__user').all()
    serializer_class = BookingSerializer

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateBookingSerializer
        return BookingSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        slot_start = serializer.validated_data['slot']
        room_type = serializer.validated_data['room_type']
        user_ids = serializer.validated_data.get('user_ids', [])
        team = serializer.validated_data.get('team_id', None)

        users = list(user_ids) if user_ids else []
        
        try:
            booking = book_slot(slot_start=slot_start, room_type=room_type, users=users, team=team)
        except BookingError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        output_serializer = BookingSerializer(booking).data
        return Response({
                "message": "Booking successful",
                "booking": output_serializer,
                "booking_code": booking.booking_code,
            }, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['post'], url_path='cancel')
    def cancel(self, request):
        """
        Cancel a booking using booking_code.
        Optional user_id for shared desk partial cancel.
        """
        booking_code = request.data.get('booking_code')
        user_id = request.data.get('user_id')
        if not booking_code:
            raise ValidationError({"booking_code": "This field is required."})
        
        user = None
        if user_id:
            try:
                user = Users.objects.get(id=user_id)
            except Users.DoesNotExist:
                raise ValidationError({"user_id": "User not found."})

        try:
            cancel_booking(booking_code, user=user)
        except BookingError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({"message": "Booking cancelled successfully."}, status=status.HTTP_200_OK)
    
@api_view(['GET'])
def available_rooms(request):
    """
    Return available rooms for a given slot.
    Example:
    GET /api/v1/rooms/available/?slot=2025-10-14T10:00:00
    """
    slot_str = request.query_params.get('slot')
    if not slot_str:
        return Response({"detail": "slot query parameter is required."}, status=status.HTTP_400_BAD_REQUEST)
    slot_start = parse_datetime(slot_str)
    if not slot_start:
        return Response({"detail": "Invalid datetime format for slot."}, status=status.HTTP_400_BAD_REQUEST)
    # Private and Conference rooms
    occupied_rooms_id = Bookings.objects.filter(slot_start=slot_start).values_list('room_id', flat=True)
    private_rooms = Rooms.objects.filter(room_type=RoomType.PRIVATE).exclude(id__in=occupied_rooms_id)
    conference_rooms = Rooms.objects.filter(room_type=RoomType.CONFERENCE).exclude(id__in=occupied_rooms_id)
    # Shared rooms
    shared_rooms = Rooms.objects.filter(room_type=RoomType.SHARED).annotate(
        used_seats=Count('bookings__attendees', filter=Q(bookings__slot_start=slot_start) & ~Q(bookings__attendees__user__age__lt=10)) 
        )
    shared_rooms_available = []
    for room in shared_rooms:
        remanining_seats = max((room.capacity - (room.used_seats or 0)), 0)
        shared_rooms_available.append({
            "room_id": room.id,
            "room_number": room.room_number,
            "remaining_seats": remanining_seats
        })

    return Response({
        "slot" : slot_start,
        "private_rooms" : list(private_rooms.values('id', 'room_number', 'capacity')),
        "conference_rooms" : list(conference_rooms.values('id', 'room_number', 'capacity')),
        "shared_rooms" : shared_rooms_available
    }, status=status.HTTP_200_OK)