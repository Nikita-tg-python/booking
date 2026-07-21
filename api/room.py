from fastapi import APIRouter

from database import SessionDep
from models.room import RoomAdd, RoomUpdate
from services.register import CurrentUserDep
from services.room import (
    process_delete_room,
    process_get_room,
    process_new_room,
    process_update_room,
)

room = APIRouter(prefix="/rooms", tags=["Room"])


@room.get("/{room_id}", response_model=RoomAdd)
async def get_room(room_id: int, db: SessionDep):
    return await process_get_room(room_id=room_id, db=db)


@room.post("/", response_model=RoomAdd)
async def new_room(room: RoomAdd, current_user: CurrentUserDep, db: SessionDep):
    return await process_new_room(room_data=room, user_id=current_user.id, db=db)


@room.delete("/{room_id}")
async def delete_room(room_id: int, current_user: CurrentUserDep, db: SessionDep):
    return await process_delete_room(room_id=room_id, user_id=current_user.id, db=db)


@room.patch("/{room_id}", response_model=RoomAdd)
async def update_room(
    room_id: int, room: RoomUpdate, current_user: CurrentUserDep, db: SessionDep
):
    return await process_update_room(
        room_id=room_id, room_data=room, user_id=current_user.id, db=db
    )
