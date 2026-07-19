from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from models.booking import Booking
    from models.hotel import Hotel


class RoomBase(SQLModel):
    room_number: str
    adults: int
    children: int = Field(default=0)
    bed: str
    price: int = Field(index=True)


class Room(RoomBase, table=True):
    id: int | None = Field(default=None, primary_key=True)

    hotel_id: int | None = Field(default=None, foreign_key="hotel.id")
    hotel: "Hotel" = Relationship(back_populates="rooms")

    bookings: "Booking" = Relationship(back_populates="room")


class RoomUpdate(SQLModel):
    room_number: str | None
    adults: int | None
    children: int | None
    bed: str | None
    price: int | None = Field(index=True)
