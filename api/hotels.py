from fastapi import APIRouter, Depends, Request

from cache import cache_response
from database import SessionDep
from models.hotel import HotelBase, HotelFilter, HotelUpdate
from services.hotels import (
    new_hotel,
    process_delete_hotel,
    process_get_hotel,
    process_get_hotels,
    process_get_my_hotels,
    process_get_rooms,
    update_hotel,
)
from services.register import CurrentUserDep

hotel = APIRouter(prefix="/hotels", tags=["Hotel"])


@hotel.get("/")
@cache_response(expire_minutes=5)
async def hotels(request: Request, db: SessionDep, filters: HotelFilter = Depends()):
    return await process_get_hotels(filters=filters, db=db)


@hotel.get("/my")
async def get_my_hotels(current_user: CurrentUserDep, db: SessionDep):
    return await process_get_my_hotels(user_id=current_user.id, db=db)


@hotel.get("/rooms")
async def get_rooms(hotel_id: int, db: SessionDep):
    return await process_get_rooms(hotel_id=hotel_id, db=db)


@hotel.get("/{hotel_id}")
async def get_hotel(hotel_id: int, db: SessionDep):
    return await process_get_hotel(hotel_id=hotel_id, db=db)


@hotel.post("/add")
async def add_hotel(
    hotel_data: HotelBase, current_user: CurrentUserDep, db: SessionDep
):
    return await new_hotel(hotel_data=hotel_data, user_id=current_user.id, db=db)


@hotel.delete("/{hotel_id}")
async def delete_hotel(hotel_id: int, current_user: CurrentUserDep, db: SessionDep):
    return await process_delete_hotel(hotel_id=hotel_id, user_id=current_user.id, db=db)


@hotel.patch("/{hotel_id}")
async def patch_hotel(
    hotel_id: int,
    hotel_update: HotelUpdate,
    current_user: CurrentUserDep,
    db: SessionDep,
):
    return await update_hotel(
        hotel_id=hotel_id, hotel_updata=hotel_update, user_id=current_user.id, db=db
    )
