import asyncio
from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from app.cache import delete_cache, get_cache, set_cache
from app.database import SessionDep, setting
from models.register import (
    SuperUser,
    Token,
    TokenUser,
    UserBase,
    UserRegister,
    UserUpdate,
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


class AuthService:
    REFRESH_TOKEN_TIME = 7
    ACCESS_TOKEN_TIME = 15
    ALGORITHM = "HS256"

    def __init__(self, db: SessionDep) -> None:
        self.db = db
        self.pwd_context = PasswordHash.recommended()

    async def hash_pwd(self, pwd: str):
        return await asyncio.to_thread(self.pwd_context.hash, pwd)

    async def verify_pwd(self, pwd: str, hash_pwd: str):
        return await asyncio.to_thread(self.pwd_context.verify, pwd, hash_pwd)

    async def jwt_decoder(self, data: str):
        return await asyncio.to_thread(
            jwt.decode, data, setting.key, algorithms=[self.ALGORITHM]
        )

    async def jwt_encoder(self, data: dict):
        return await asyncio.to_thread(
            jwt.encode, data, setting.key, algorithm=self.ALGORITHM
        )

    async def get_user(self, email: str) -> SuperUser | None:
        resault = await self.db.exec(select(SuperUser).where(SuperUser.email == email))
        return resault.first()

    async def auth_user(self, email: str, pwd: str) -> SuperUser | None:
        user = await self.get_user(email=email)
        if not user:
            await self.verify_pwd(pwd, self.pwd_context.hash("dummypasword"))
            return None
        verefi_user = await self.verify_pwd(pwd, user.hashed_password)
        if not verefi_user:
            return None
        return user

    async def create_access_token(self, user: dict):
        to_encode = user.copy()
        expire = datetime.now(timezone.utc) + timedelta(minutes=self.ACCESS_TOKEN_TIME)

        to_encode.update({"exp": expire, "type": "access"})
        encode_jwt = await self.jwt_encoder(to_encode)

        return encode_jwt

    async def create_refresh_token(self, user: dict):
        to_encode = user.copy()
        expire = datetime.now(timezone.utc) + timedelta(days=self.REFRESH_TOKEN_TIME)

        to_encode.update({"exp": expire, "type": "refresh"})
        encode_jwt = await self.jwt_encoder(to_encode)

        return encode_jwt

    async def get_current_user(self, token: str):
        creditials_exeption = HTTPException(
            status_code=401,
            detail="Could not validate",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = await self.jwt_decoder(token)
            user_id = payload.get("id")
            is_superuser = payload.get("superuser")
            token_type = payload.get("type")

            if user_id is None or token_type != "access":
                raise creditials_exeption

            return TokenUser(id=user_id, is_superuser=is_superuser)

        except InvalidTokenError:
            raise creditials_exeption


async def get_auth_server(db: SessionDep):
    return AuthService(db=db)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_server)]


async def get_active_user(
    token: Annotated[str, Depends(oauth2_scheme)], auth_user: AuthServiceDep
):

    return await auth_user.get_current_user(token=token)


CurrentUserDep = Annotated[TokenUser, Depends(get_active_user)]


async def process_login(email: str, password: str, auth_user: AuthServiceDep):
    user_dict = await auth_user.auth_user(
        email=email,
        pwd=password,
    )

    if user_dict is None:
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    access_token = await auth_user.create_access_token(
        user={"id": user_dict.id, "superuser": user_dict.superuser}
    )

    data = {"id": user_dict.id, "superuser": user_dict.superuser}

    refresh_token = await auth_user.create_refresh_token(user=data)

    await set_cache(
        key=f"refresh_token:{user_dict.email}", value=refresh_token, expire_days=7
    )

    return Token(
        access_token=access_token, refresh_token=refresh_token, token_type="bearer"
    )


async def process_refresh_token(refresh_token_in: str, auth_user) -> Token:
    creditials_exeption = HTTPException(
        status_code=401,
        detail="Invalid refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = await auth_user.jwt_decoder(refresh_token_in)
        user_email = payload.get("email")
        token_type = payload.get("type")

        if user_email is None or token_type != "refresh":
            raise creditials_exeption

    except InvalidTokenError:
        raise creditials_exeption

    refresh_token = await get_cache(key=f"refresh_token:{user_email}")

    if refresh_token != refresh_token_in:
        raise creditials_exeption

    user = await auth_user.get_user(email=user_email)

    if not user:
        raise creditials_exeption

    data = {"email": user.email, "superuser": user.superuser}

    new_eccess_token = await auth_user.create_access_token(user=data)
    new_refresh_token = await auth_user.create_refresh_token(user=data)

    await delete_cache(key=user_email)
    await set_cache(
        key=f"refresh_token:{user_email}", value=new_refresh_token, expire_days=7
    )

    return Token(
        access_token=new_eccess_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
    )


async def process_register(user_data: UserRegister, auth_user, db):

    user_db = await auth_user.get_user(email=user_data.email)

    if user_db:
        raise HTTPException(status_code=409, detail="User already exists")

    hashed_password = await auth_user.hash_pwd(user_data.password)

    user = SuperUser(
        name=user_data.name,
        surname=user_data.surname,
        patronymic=user_data.patronymic,
        email=user_data.email,
        hashed_password=hashed_password,
        superuser=False,
    )

    db.add(user)

    try:
        await db.commit()
        await db.refresh(user)

    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=409, detail="User with this email already exists"
        )

    return user


async def get_user(id: int, db: SessionDep):

    user_cache = await get_cache(f"user:{id}")

    if user_cache:
        return user_cache

    user_db = await db.get(SuperUser, id)

    if user_db is None:
        raise HTTPException(status_code=404, detail="User not found")

    user = UserBase.model_validate(user_db)

    await set_cache(
        key=f"user:{user_db.id}", value=user.model_dump(mode="json"), expire_minutes=10
    )

    return user


async def process_user_rename(user: UserUpdate, id: int, db: SessionDep):
    update_user = user.model_dump(exclude_unset=True)

    user_db = await db.get(SuperUser, id)

    if user_db is None:
        raise HTTPException(status_code=404, detail="User not found")

    user_db.sqlmodel_update(update_user)
    db.add(user_db)

    try:
        await db.commit()
        await db.refresh(user_db)

    except IntegrityError:
        await db.rollback()

        raise HTTPException(
            status_code=409, detail="User with this email already exists"
        )

    await delete_cache(str(user_db.id))

    return user_db


async def new_password(pwd: str, new_pwd: str, id: int, auth_service, db):

    user_db = await db.get(SuperUser, id)

    if user_db is None:
        raise HTTPException(status_code=404, detail="User not found")

    if not await auth_service.verify_pwd(pwd, user_db.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect password")

    new_hashed_password = await auth_service.hash_pwd(new_pwd)
    user_db.hashed_password = new_hashed_password

    db.add(user_db)
    await db.commit()
    await db.refresh(user_db)

    await delete_cache(str(user_db.id))
    return user_db
