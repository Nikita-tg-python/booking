import json
from datetime import timedelta
from functools import wraps
from typing import Any

import redis.asyncio as redis
from fastapi import Request
from fastapi.encoders import jsonable_encoder

from app.database import setting

redis_client = redis.from_url(setting.redis_cache_url, decode_responses=True)


async def set_cache(
    key: str,
    value: Any,
    expire_days: int = 0,
    expire_hours: int = 0,
    expire_minutes: int = 0,
) -> None:
    if isinstance(value, (dict, list)):
        value = json.dumps(value)

    time = timedelta(days=expire_days, hours=expire_hours, minutes=expire_minutes)

    if time.total_seconds() == 0:
        time = timedelta(seconds=60)
    await redis_client.set(name=key, value=value, ex=time)


async def get_cache(key: str) -> Any | None:
    data = await redis_client.get(key)
    if not data:
        return None

    try:
        return json.loads(data)
    except (json.JSONDecodeError, TypeError):
        return data


async def delete_cache(key: str) -> None:
    await redis_client.delete(key)


async def clear_cache(prefix: str):
    keys_to_delete = []
    async for key in redis_client.scan_iter(match=f"{prefix}"):
        keys_to_delete.append(key)

    if keys_to_delete:
        await redis_client.delete(*keys_to_delete)


def cache_response(expire_minutes: int = 5):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):

            request: Request | None = kwargs.get("request")
            if not request:
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break

            if request:
                query_params = sorted(request.items())
                params_str = ":".join(f"{k}={v}" for k, v in query_params if v)
                cache_key = (
                    f"{request.url.path}:{params_str}"
                    if params_str
                    else request.url.path
                )
            else:
                cache_key = f"{func.__name__}:{str(kwargs)}"

            cached_data = await get_cache(cache_key)
            if cached_data is not None:
                return cached_data

            result = await func(*args, **kwargs)

            serializable_data = jsonable_encoder(result)
            await set_cache(
                key=cache_key, value=serializable_data, expire_minutes=expire_minutes
            )

            return result

        return wrapper

    return decorator
