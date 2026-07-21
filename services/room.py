from fastapi import HTTPException
from sqlmodel import select

from cache import delete_cache
from database import SessionDep
from models.hotel import Hotel
from models.room import Room, RoomAdd, RoomUpdate


async def process_get_room(room_id: int, db: SessionDep):
    room = await db.exec(select(Room).where(Room.id == room_id))
    room = room.first()

    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return room


async def process_new_room(room_data: RoomAdd, user_id: int, db: SessionDep):

    hotel = await db.exec(
        select(Hotel.id).where(Hotel.user_id == user_id, Hotel.id == room_data.hotel_id)
    )
    hotel = hotel.first()

    if not hotel:
        raise HTTPException(status_code=404, detail="Hotel not found")

    room = Room.model_validate(room_data)

    db.add(room)
    await db.commit()
    await db.refresh(room)

    await delete_cache(f"hotel_rooms:{room_data.hotel_id}")

    return room


async def process_delete_room(room_id: int, user_id: int, db: SessionDep):
    room = await db.get(Room, room_id)

    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    hotel = await db.exec(
        select(Hotel).where(Hotel.id == room.hotel_id, Hotel.user_id == user_id)
    )
    hotel = hotel.first()

    if not hotel:
        raise HTTPException(status_code=404, detail="Hotel not found")

    room.is_active = False

    db.add(room)
    await db.commit()

    await delete_cache(f"hotel_rooms:{room.hotel_id}")

    return {"message": f"Room '{room.room_number}' deleted successfully"}


async def process_update_room(
    room_id: int, room_data: RoomUpdate, user_id: int, db: SessionDep
):
    room = await db.get(Room, room_id)

    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    hotel = await db.exec(
        select(Hotel).where(Hotel.id == room.hotel_id, Hotel.user_id == user_id)
    )
    hotel = hotel.first()

    if not hotel:
        raise HTTPException(status_code=404, detail="Hotel not found")

    update_data = room_data.model_dump(exclude_unset=True)

    room.sqlmodel_update(update_data)

    db.add(room)
    await db.commit()
    await db.refresh(room)

    await delete_cache(f"hotel_rooms:{room.hotel_id}")

    return room
