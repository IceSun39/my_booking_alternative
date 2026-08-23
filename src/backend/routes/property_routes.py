from backend.models import User, Role
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.backend.core.dependencies import get_owner_or_admin_user
from src.backend.database.database import get_session
from src.backend.schemas.properties_schemas import PropertiesUpdate, PropertiesCreate, PropertiesResponse
from src.backend.services import PropertyService
from typing import List

properties_router = APIRouter(
    prefix="/api/properties",
    tags=["properties"],
)

PropertyService = PropertyService()


async def check_owner(
        session: AsyncSession,
        owner: User,
        property_id: int
) -> bool:
    existing_property = await PropertyService.get_property(session=session, property_id=property_id)
    if existing_property.owner_id == owner.user_id:
        return True
    raise HTTPException(
        status_code=403,
        detail="Access Denied",
    )


@properties_router.get("/{property_id}", response_model=PropertiesResponse)
async def get_property(property_id: int, session: AsyncSession = Depends(get_session)):
    """Отримати готель по id"""
    return await PropertyService.get_property(session=session, property_id=property_id)


@properties_router.get("/", response_model=List[PropertiesResponse])
async def get_all_properties(session: AsyncSession = Depends(get_session)):
    """Отримати список всіх готелів"""
    return await PropertyService.get_all_properties(session=session)


@properties_router.post("/", response_model=PropertiesResponse)
async def create_property(
        property_create: PropertiesCreate,
        session: AsyncSession = Depends(get_session),
        current_user: User = Depends(get_owner_or_admin_user)
):
    """Створити власність, може тільки адмін або власник"""
    if current_user.role in [Role.ADMIN, Role.OWNER]:
        return await PropertyService.create_property(session=session, properties_create=property_create)
    raise HTTPException(
        status_code=403,
        detail="Access Denied",
    )


@properties_router.put("/{property_id}", response_model=PropertiesResponse)
async def update_property(
        property_id: int,
        property_update: PropertiesUpdate,
        session: AsyncSession = Depends(get_session),
        current_user: User = Depends(get_owner_or_admin_user)
):
    """"Оновити дані про власність"""
    if await check_owner(session=session, owner=current_user, property_id=property_id):
        return PropertyService.update_property(session=session, property_id=property_id, properties_update=property_update)
    raise HTTPException(
        status_code=403,
        detail="Access Denied",
    )


@properties_router.delete("/{property_id}", response_model=PropertiesResponse, status_code=204)
async def delete_property(
        property_id: int,
        session: AsyncSession = Depends(get_session),
        current_user: User = Depends(get_owner_or_admin_user)
):
    """Видалити власність"""
    if await check_owner(session=session, owner=current_user, property_id=property_id) or current_user.is_admin:
        await PropertyService.delete_property(session=session, property_id=property_id)
    raise HTTPException(
        status_code=403,
        detail="Access Denied",
    )
