from datetime import date
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from models.room import Room


class BookingBase(SQLModel):
    date_from: date
    date_to: date
    total_price: int


class Booking(BookingBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    room_id: Optional[int] = Field(default=None, foreign_key="room.id")
    room: Optional["Room"] = Relationship(back_populates="bookings")
