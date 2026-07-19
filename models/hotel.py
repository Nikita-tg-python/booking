from typing import TYPE_CHECKING, List

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from models.register import SuperUser
    from models.room import Room


class HotelBase(SQLModel):
    name: str = Field(unique=True, index=True)
    country: str = Field(index=True)
    city: str = Field(index=True)
    address: str
    grade: int = Field(index=True, ge=1, le=5)
    restaurant: bool
    gym: bool


class HotelFilter(SQLModel):
    country: str | None
    city: str | None
    grade: int | None
    restaurant: bool | None
    gym: bool | None


class Hotel(HotelBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    is_active: bool = True
    user_id: int = Field(foreign_key="superuser.id")

    rooms: List["Room"] = Relationship(back_populates="hotel")
    user: "SuperUser" = Relationship(back_populates="hotels")


class HotelUpdate(SQLModel):
    name: str | None
    restaurant: bool | None
    gym: bool | None
