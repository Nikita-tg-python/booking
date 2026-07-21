from typing import TYPE_CHECKING

from pydantic import EmailStr
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from models.booking import Booking
    from models.hotel import Hotel


class UserBase(SQLModel):
    name: str = Field(index=True)
    surname: str = Field(index=True)
    patronymic: str
    email: EmailStr = Field(index=True, unique=True)


class UserRegister(SQLModel):
    name: str = Field(index=True)
    surname: str = Field(index=True)
    patronymic: str
    email: EmailStr = Field(index=True, unique=True)
    password: str = Field(min_length=6)


class UserUpdate(SQLModel):
    name: str | None = Field(default=None, index=True)
    surname: str | None = Field(default=None, index=True)
    patronymic: str | None = None
    email: EmailStr | None = Field(default=None, index=True, unique=True)


class User(UserBase):
    hashed_password: str


class UserPassword(SQLModel):
    password: str = Field(min_length=6)
    new_password: str = Field(min_length=6)


class SuperUser(User, table=True):
    id: int | None = Field(default=None, primary_key=True)
    superuser: bool = False

    points: int = 10000

    hotels: list["Hotel"] = Relationship(back_populates="user")
    bookings: list["Booking"] = Relationship(back_populates="user")


class Token(SQLModel):
    access_token: str
    refresh_token: str
    token_type: str


class TokenUser(SQLModel):
    id: int
    is_superuser: bool | None = False


class RefredhTokenRequest(SQLModel):
    refresh_token: str
