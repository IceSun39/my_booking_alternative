import os
from dotenv import load_dotenv
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from starlette import status
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.database.database import get_session
from src.backend.core.security import decode_token
from src.backend.services.user_services import UserService
from src.backend.models.users import User, Role

load_dotenv()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
UserService = UserService()


async def get_current_user(token: str = Depends(oauth2_scheme),
                           session: AsyncSession = Depends(get_session)) -> User:
    payload = decode_token(token)

    if payload.get("refresh") is True:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Please use an access token, not a refresh token",
        )

    email = payload.get("sub")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token structure: missing sub",
        )

    user = UserService.get_user_by_email(session, email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user


async def get_owner_or_admin_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in [Role.ADMIN, Role.OWNER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to perform this action",
        )
    return current_user


async def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to perform this action",
        )
    return current_user
