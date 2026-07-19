from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from app.cache import clear_cache, delete_cache, get_cache, set_cache
from app.database import SessionDep
from models.hotel import Hotel, HotelBase, HotelFilter, HotelUpdate


async def process_get_hotels(filters: HotelFilter, db: SessionDep):

    query = select(Hotel)

    active_filters = filters.model_dump(exclude_none=True)

    for key, value in active_filters.items():
        query = query.where(getattr(Hotel, key) == value)

    hotels = await db.exec(query)

    return hotels.all()


async def process_get_hotel(id: int, db: SessionDep):

    hotel = await get_cache(f"hotel:{id}")

    if hotel:
        return hotel

    hotel = await db.get(Hotel, id)

    if not hotel:
        raise HTTPException(status_code=404, detail="Hotel not found")

    await set_cache(
        key=f"hotel:{id}", value=hotel.model_dump(mode="json"), expire_minutes=10
    )
    return hotel


async def process_get_my_hotels(id: int, db: SessionDep):

    hotels = await db.exec(select(Hotel).where(Hotel.user_id == id))

    hotels = hotels.all()

    if not hotels:
        raise HTTPException(status_code=404, detail="You don't have hotel")

    return hotels


async def new_hotel(hotel_data: HotelBase, id: int, db: SessionDep):

    hotel = Hotel.model_validate(hotel_data, update={"user_id": id})

    hotel.is_active = True

    db.add(hotel)
    try:
        await db.commit()
        await db.refresh(hotel)

    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=409, detail="Hotel with this name already exists"
        )

    await clear_cache("/hotels")

    return hotel


async def process_delete_hotel(id: int, user_id: int, db: SessionDep):

    hotel = await db.exec(select(Hotel).where(Hotel.id == id, Hotel.user_id == user_id))

    hotel = hotel.first()

    if not hotel:
        raise HTTPException(status_code=404, detail="Hotel not found")

    hotel.is_active = False

    await delete_cache(f"hotel:{id}")

    db.add(hotel)
    await db.commit()
    await db.refresh(hotel)

    await clear_cache("/hotels")

    return {"message": f"Hotel '{hotel.name}' has been successfully deleted"}


async def update_hotel(
    id: int, hotel_updata: HotelUpdate, user_id: int, db: SessionDep
):
    hotel_data = await db.exec(
        select(Hotel).where(Hotel.id == id, Hotel.user_id == user_id)
    )

    hotel_data = hotel_data.first()

    if not hotel_data:
        raise HTTPException(status_code=404, detail="Hotel not found")

    hotel = hotel_updata.model_dump(exclude_unset=True)

    hotel_data.sqlmodel_update(hotel)

    await delete_cache(key=f"hotel{id}")

    db.add(hotel_data)
    await db.commit()
    await db.refresh(hotel_data)

    return hotel_data
