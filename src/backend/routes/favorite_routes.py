from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from src.backend.database.database import get_session
from src.backend.core.dependencies import get_current_user
from src.backend.models.users import User
from src.backend.schemas.favorites_schemas import FavoriteCreate, FavoriteResponse
from src.backend.services.favorite_services import FavoriteService

favorites_router = APIRouter(
    prefix="/api/favorites",
    tags=["favorites"]
)

favorite_service = FavoriteService()

@favorites_router.get("/", response_model=List[FavoriteResponse])
async def get_my_favorites(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Отримати список улюблених готелів поточного користувача"""
    return await favorite_service.get_users_favorites(session, current_user.user_id)

@favorites_router.post("/", response_model=FavoriteResponse, status_code=status.HTTP_201_CREATED)
async def add_to_favorites(
    favorite_data: FavoriteCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Додати готель до обраного"""
    return await favorite_service.create_favorite(session, current_user.user_id, favorite_data)

@favorites_router.delete("/{property_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_favorites(
    property_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Видалити готель з обраного"""
    await favorite_service.delete_favorite(session, current_user.user_id, property_id)
