from datetime import date
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from models.register import SuperUser
    from models.room import Room


class BookingBase(SQLModel):
    date_from: date
    date_to: date
    total_price: int


class Booking(BookingBase, table=True):
    id: int | None = Field(default=None, primary_key=True)

    room_id: int = Field(foreign_key="room.id")
    room: "Room" = Relationship(back_populates="bookings")

    user_id: int = Field(foreign_key="superuser.id")
    user: "SuperUser" = Relationship(back_populates="bookings")
