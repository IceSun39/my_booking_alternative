from src.backend.models import User
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.services.user_services import UserService
from src.backend.schemas.users_schemas import UserResponse, UserCreate, UserUpdate
from src.backend.database.database import get_session
from src.backend.core.dependencies import get_current_user, get_admin_user

user_router = APIRouter(
    prefix="/api/user",
    tags=["user"],
)
user_service = UserService()


@user_router.get("/me", response_model=UserResponse)
async def get_me(session: AsyncSession = Depends(get_session),
                 current_user: User = Depends(get_current_user)):
    return current_user


@user_router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, session: AsyncSession = Depends(get_session),
                   current_user: User = Depends(get_current_user)):
    if not current_user.is_admin and current_user.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not an administrator"
        )
    return await user_service.get_user(user_id=user_id, session=session)


@user_router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user_create: UserCreate, session: AsyncSession = Depends(get_session),
                      user: User = Depends(get_admin_user)):
    return await user_service.create_user(user_create=user_create, session=session)


@user_router.put("/{user_id}", response_model=UserResponse)
async def update_user(user_id: int, user_update: UserUpdate, session: AsyncSession = Depends(get_session),
                      current_user: User = Depends(get_current_user)):
    if not current_user.is_admin and current_user.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not an administrator"
        )
    return await user_service.update_user(user_id=user_id, user_update=user_update, session=session)


@user_router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, session: AsyncSession = Depends(get_session),
                      current_user: User = Depends(get_current_user)):
    if not current_user.is_admin and current_user.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not an administrator"
        )
    await user_service.delete_user(user_id=user_id, session=session)
