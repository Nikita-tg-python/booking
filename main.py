from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlmodel import SQLModel

from api.booking import booking
from api.hotels import hotel
from api.register import reg
from api.room import room
from cache import redis_client
from database import engine


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

app.include_router(room)

app.include_router(booking)
