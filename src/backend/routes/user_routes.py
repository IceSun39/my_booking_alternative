from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.core.security import create_access_token, decode_token, get_password_hash, verify_password
from src.backend.services.user_services import UserService
from src.backend.schemas.users_schemas import UserResponse, UserCreate
from src.backend.database.database import get_session