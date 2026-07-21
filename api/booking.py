from fastapi import APIRouter

from database import SessionDep
from models.booking import BookingRent
from services.booking import (
    process_create_booking,
    process_delete_booking,
    process_get_booking,
    process_get_my_bookings,
)
from services.register import CurrentUserDep

booking = APIRouter(prefix="/booking", tags=["Booking"])


@booking.get("/my")
async def get_my_bookings(current_user: CurrentUserDep, db: SessionDep):
    return await process_get_my_bookings(user_id=current_user.id, db=db)


@booking.post("/calculate")
async def get_booking(booking: BookingRent, db: SessionDep):
    return await process_get_booking(booking=booking, db=db)


@booking.post("/")
async def create_booking(
    booking: BookingRent, current_user: CurrentUserDep, db: SessionDep
):
    return await process_create_booking(booking=booking, user_id=current_user.id, db=db)


@booking.delete("/{booking_id}")
async def delete_booking(booking_id: int, current_user: CurrentUserDep, db: SessionDep):
    return await process_delete_booking(
        booking_id=booking_id, user_id=current_user.id, db=db
    )
