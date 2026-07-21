from typing import Annotated

from fastapi import Depends
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import Select, event
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import ORMExecuteState, Session
from sqlmodel import col
from sqlmodel.ext.asyncio.session import AsyncSession

from models.hotel import Hotel
from models.room import Room


class Setting(BaseSettings):
    db: str
    key: str
    postgres_password: str
    redis_cache_url: str
    redis_celery_url: str
    model_config = SettingsConfigDict(env_file=".env")


setting = Setting()  # type: ignore
engine = create_async_engine(setting.db)


async def get_session():
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session


@event.listens_for(Session, "do_orm_execute")
def automatic_soft_delete_filter(execute_state: ORMExecuteState):
    if isinstance(execute_state.statement, Select):
        for column in execute_state.statement.column_descriptions:
            entity = column.get("entity")

            if entity is not None and entity in (Room, Hotel):
                execute_state.statement = execute_state.statement.where(
                    col(entity.is_active)
                )


SessionDep = Annotated[AsyncSession, Depends(get_session)]
