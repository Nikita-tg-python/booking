from datetime import date
from typing import TYPE_CHECKING

from pydantic import model_validator
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from models.register import SuperUser
    from models.room import Room


class BookingBase(SQLModel):
    date_from: date
    date_to: date
    total_days: int
    total_price: int


class Booking(BookingBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    is_active: bool = True

    room_id: int = Field(foreign_key="room.id")
    room: "Room" = Relationship(back_populates="bookings")

    user_id: int = Field(foreign_key="superuser.id")
    user: "SuperUser" = Relationship(back_populates="bookings")


class BookingRent(SQLModel):
    date_from: date
    date_to: date
    room_id: int

    @model_validator(mode="after")
    def check_dates(self):
        if self.date_from >= self.date_to:
            raise ValueError("Дата выезда должна быть строго позже даты заезда!")

        if self.date_from < date.today():
            raise ValueError("Нельзя забронировать на прошедшую дату!")

        return self
