def validate_room_number(room: str) -> bool:
    room = room.strip()
    return 1 <= len(room) <= 10


def validate_quantity(value: str) -> bool:
    if not value.isdigit():
        return False
    num = int(value)
    return 1 <= num <= 20

