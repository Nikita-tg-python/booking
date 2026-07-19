from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlmodel import SQLModel

from app.api.hotels import hotel
from app.api.register import reg
from app.cache import redis_client
from app.database import engine
from models.booking import Booking
from models.hotel import Hotel
from models.room import Room


async def create_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def close_db():
    await engine.dispose()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db()
    await redis_client.ping()

    yield

    await close_db()
    await redis_client.close()


app = FastAPI(lifespan=lifespan)

app.include_router(reg)
app.include_router(hotel)


@app.get("/1")
def get_1(r: Room):
    return r


@app.get("/2")
def get_2(b: Booking):
    return b


@app.get("/3")
def get_3(h: Hotel):
    return h
