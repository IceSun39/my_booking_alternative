from backend.models import User
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.services import PropertyService
from src.backend.schemas.properties_schemas import PropertiesUpdate, PropertiesCreate, PropertiesResponse
from src.backend.database.database import get_session
from src.backend.core.dependencies import get_admin_user
from typing import List

properties_router = APIRouter(
    prefix="/api/properties",
    tags=["properties"],
)

PropertyService = PropertyService()


@properties_router.get("/{property_id}", response_model=PropertiesResponse)
async def get_property(property_id: int, session: AsyncSession = Depends(get_session)):
    return await PropertyService.get_property(session=session, property_id=property_id)


@properties_router.get("/", response_model=List[PropertiesResponse])
async def get_all_properties(session: AsyncSession = Depends(get_session)):
    return await PropertyService.get_all_properties(session=session)


@properties_router.post("/", response_model=PropertiesResponse)
async def create_property(
        property_create: PropertiesCreate,
        session: AsyncSession = Depends(get_session),
        admin: User = Depends(get_admin_user)
):
    return await PropertyService.create_property(session=session, properties_create=property_create)


@properties_router.put("/{property_id}", response_model=PropertiesResponse)
async def update_property(
        property_id: int,
        property_update: PropertiesUpdate,
        session: AsyncSession = Depends(get_session),
        admin: User = Depends(get_admin_user)
):
    return await PropertyService.update_property(
        session=session,
        properties_update=property_update,
        property_id=property_id
    )


@properties_router.delete("/{property_id}", response_model=PropertiesResponse)
async def delete_property(
        property_id: int,
        session: AsyncSession = Depends(get_session),
        admin: User = Depends(get_admin_user)
):
    return await PropertyService.delete_property(session=session, property_id=property_id)
