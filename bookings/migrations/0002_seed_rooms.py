from django.db import migrations

def seed_rooms(apps, schema_editor):
    Room = apps.get_model('bookings', 'Rooms')
    data = []
    # 8 Private Rooms
    for i in range(1, 9):
        data.append(Room(room_number=f'P{i}', room_type='private', capacity=1))
    # 4 Conference Rooms
    for i in range(1, 5):
        data.append(Room(room_number=f'C{i}', room_type='conference', capacity=10))
    # 3 Shared Desks
    for i in range(1, 4):
        data.append(Room(room_number=f'S{i}', room_type='shared', capacity=4))
    Room.objects.bulk_create(data)

class Migration(migrations.Migration):
    dependencies = [
        ('bookings', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_rooms),
    ]