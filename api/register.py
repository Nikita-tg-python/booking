from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pwdlib import PasswordHash

from database import SessionDep
from models.register import (
    RefredhTokenRequest,
    UserBase,
    UserPassword,
    UserRegister,
    UserUpdate,
)
from services.register import (
    AuthServiceDep,
    CurrentUserDep,
    get_user,
    new_password,
    process_login,
    process_refresh_token,
    process_register,
    process_user_rename,
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

password_hash = PasswordHash.recommended()

DUMMY_HASH = password_hash.hash("dummypasword")

reg = APIRouter(tags=["Auth"])


@reg.post("/login")
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    auth_user: AuthServiceDep,
):
    return await process_login(
        email=form_data.username, password=form_data.password, auth_user=auth_user
    )


@reg.post("/refresh")
async def refresh_token(request: RefredhTokenRequest, auth_user: AuthServiceDep):
    return await process_refresh_token(
        refresh_token_in=request.refresh_token, auth_user=auth_user
    )


@reg.post("/register")
async def register(
    user_data: UserRegister, auth_user: AuthServiceDep, db: SessionDep
) -> UserBase:
    return await process_register(user_data=user_data, auth_user=auth_user, db=db)


@reg.get("/users/me")
async def get_login_user(current_user: CurrentUserDep, db: SessionDep) -> UserBase:
    return await get_user(user_id=current_user.id, db=db)


@reg.patch("/users/update")
async def user_rename(
    user: UserUpdate,
    current_user: CurrentUserDep,
    db: SessionDep,
) -> UserBase:
    return await process_user_rename(user=user, user_id=current_user.id, db=db)


@reg.patch("/users/password/me")
async def password(
    user_passwords: UserPassword,
    current_user: CurrentUserDep,
    auth_service: AuthServiceDep,
    db: SessionDep,
) -> UserBase:
    return await new_password(
        pwd=user_passwords.password,
        new_pwd=user_passwords.new_password,
        user_id=current_user.id,
        auth_service=auth_service,
        db=db,
    )
