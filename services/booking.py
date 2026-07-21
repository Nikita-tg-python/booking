from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from database import SessionDep
from models.booking import Booking, BookingBase, BookingRent
from models.register import SuperUser
from models.room import Room
from worker import send_booking_email


async def process_get_booking(booking: BookingRent, db: SessionDep):
    room_price = await db.exec(select(Room.price).where(Room.id == booking.room_id))

    room_price = room_price.first()

    if not room_price:
        raise HTTPException(status_code=404, detail="Room not found")

    total_days = (booking.date_to - booking.date_from).days
    total_price = total_days * room_price
    booking_data = BookingBase(
        **booking.model_dump(), total_days=total_days, total_price=total_price
    )

    return booking_data


async def process_get_my_bookings(user_id: int, db: SessionDep):
    bookings = await db.exec(select(Booking).where(Booking.user_id == user_id))

    bookings = bookings.all()

    return bookings


async def process_create_booking(booking: BookingRent, user_id: int, db: SessionDep):
    room = await db.exec(
        select(Room).where(Room.id == booking.room_id).with_for_update()
    )

    room = room.first()

    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    booking_data = await db.exec(
        select(Booking)
        .where(
            Booking.date_from < booking.date_to,
            Booking.date_to > booking.date_from,
            Booking.room_id == booking.room_id,
        )
        .with_for_update()
    )

    booking_data = booking_data.first()
    if booking_data:
        raise HTTPException(status_code=409, detail="Room busy")

    total_days = (booking.date_to - booking.date_from).days
    total_price = total_days * room.price

    user = await db.exec(
        select(SuperUser).where(SuperUser.id == user_id).with_for_update()
    )
    user = user.first()

    if not user or user.points < total_price:
        raise HTTPException(status_code=402, detail="You don't have points")

    booking_db = Booking(
        **booking.model_dump(),
        total_days=total_days,
        total_price=total_price,
        user_id=user_id,
    )

    user.points -= total_price

    db.add(booking_db)
    db.add(user)
    try:
        await db.commit()
        await db.refresh(booking_db)

        assert booking_db.id
        send_booking_email.delay(
            email=user.email,
            room=room.room_number,
            date_from=booking_db.date_from,
            date_to=booking_db.date_to,
            total_price=total_price,
            booking_id=booking_db.id,
        )

        return booking_db
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=404, detail="Room already exist")


async def process_delete_booking(booking_id: int, user_id: int, db: SessionDep):
    booking = await db.exec(
        select(Booking)
        .where(Booking.id == booking_id, Booking.user_id == user_id)
        .with_for_update()
    )

    booking = booking.first()

    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    user = await db.exec(
        select(SuperUser).where(SuperUser.id == user_id).with_for_update()
    )
    user = user.first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.points += booking.total_price

    booking.is_active = False

    db.add(user)
    db.add(booking)

    await db.commit()

    return {"message": f"Booking deleted. Refunded {booking.total_price} points."}
