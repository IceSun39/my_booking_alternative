from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.core.security import create_access_token, decode_token

auth_router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

