from typing import Annotated

from fastapi import Depends
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession


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
    async with AsyncSession(engine) as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]
