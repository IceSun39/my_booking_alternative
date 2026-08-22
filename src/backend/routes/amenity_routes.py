from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from src.backend.database.database import get_session
from src.backend.core.dependencies import get_current_user
from src.backend.models.users import User
from src.backend.schemas.amenities_schemas import AmenityResponse, AmenityCreate, AmenityUpdate
from src.backend.services import AmenityServices

amenity_router = APIRouter(
    prefix="/api/amenity",
    tags=["amenity"],
)

