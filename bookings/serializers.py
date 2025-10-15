from rest_framework import serializers
from .models import Users, Teams, Rooms, Bookings, BookingAttendees, RoomType


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = Users
        fields = ['id', 'name', 'age', 'gender']

class TeamSerializer(serializers.ModelSerializer):
    members = UserSerializer(many=True, read_only=True)
    members_id = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Users.objects.all(), write_only=True, source='members')
    
    class Meta:
        model = Teams
        fields = ['id', 'name', 'members', 'members_id']

class BookingAttendeesSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = BookingAttendees
        fields = ['id', 'user']

class BookingSerializer(serializers.ModelSerializer):
    room = serializers.StringRelatedField()
    attendees = BookingAttendeesSerializer(many=True, read_only=True)

    class Meta:
        model = Bookings
        fields = ['id', 'room', 'slot_start', 'slot_end', 'booking_code', 'attendees']

class CreateBookingSerializer(serializers.Serializer):
    slot = serializers.DateTimeField()
    room_type = serializers.ChoiceField(choices=RoomType.choices)
    user_ids = serializers.PrimaryKeyRelatedField(many=True, queryset=Users.objects.all(), required=False)
    team_id = serializers.PrimaryKeyRelatedField(queryset=Teams.objects.all(), required=False, allow_null=True)

    def validate(self, data):
        slot = data.get('slot')
        if slot.minute != 0 or slot.second != 0:
            raise serializers.ValidationError("Slot must be on the hour (e.g., 10:00, 14:00).")
        if not (9 <= slot.hour < 18):
            raise serializers.ValidationError("Slot must be within working hours (9 AM to 6 PM).")
        return data
    
