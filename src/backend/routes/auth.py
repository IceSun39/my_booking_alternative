from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.core.security import create_access_token, verify_password
from src.backend.services.user_services import UserService
from src.backend.schemas.users_schemas import UserResponse, UserCreate
from src.backend.database.database import get_session

auth_router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

REFRESH_TOKEN_EXPIRE_DAYS = 2

UserService = UserService()


@auth_router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate, session: AsyncSession = Depends(get_session)):
    existing_user = await UserService.get_user_by_email(session, user_data.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = await UserService.create_user(session, user_data)
    return new_user


@auth_router.post("/login", status_code=status.HTTP_200_OK)
async def login_user(form_data: OAuth2PasswordRequestForm = Depends(),
                     session: AsyncSession = Depends(get_session)
                     ):
    user = await UserService.get_user_by_email(session, form_data.username)
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    access_token = create_access_token(data={'sub': user.email})
    refresh_token = create_access_token(data={'sub': user.email}, refresh=True,
                                        expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "message": "Login Successful",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "email": user.email,
                "user_id": str(user.user_id)
            }
        }
    )
