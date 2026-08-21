from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.core.security import create_access_token, decode_token, get_password_hash, verify_password
from src.backend.services.user_services import UserService
from src.backend.schemas.users_schemas import  UserResponse, UserCreate
from src.backend.database.database import get_session

auth_router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

UserService = UserService()

@auth_router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate, session: AsyncSession = Depends(get_session)):
    existing_user = await UserService.get_user_by_email(session, user_data.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = UserService.create_user(session, user_data)
    return new_user
