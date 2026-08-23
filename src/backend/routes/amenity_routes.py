from backend.models import AmenityType
from fastapi import APIRouter, Depends, status, Query, Path, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from src.backend.database.database import get_session
from src.backend.core.dependencies import get_admin_user, get_owner_or_admin_user
from src.backend.models.users import User, Role
from src.backend.schemas.amenities_schemas import AmenityResponse, AmenityCreate, AmenityUpdate, AmenityAssign
from src.backend.services import AmenityServices, RoomService

amenity_router = APIRouter(
    prefix="/api/amenity",
    tags=["amenity"],
)

property_amenity_router = APIRouter(
    prefix="/api/property/{property_id}/amenities",
    tags=["amenity"],
)

room_amenity_router = APIRouter(
    prefix="/api/rooms/{room_id}/amenities",
    tags=["amenity"],
)

AmenityServices = AmenityServices()
RoomService = RoomService()


@property_amenity_router.get("/", response_model=List[AmenityResponse], status_code=status.HTTP_200_OK)
async def get_property_amenities(
        property_id: int,
        session: AsyncSession = Depends(get_session)
):
    """Get property amenities"""
    return await AmenityServices.get_property_amenities(session, property_id)


@room_amenity_router.get("/", response_model=List[AmenityResponse], status_code=status.HTTP_200_OK)
async def get_room_amenities(
        room_id: int,
        session: AsyncSession = Depends(get_session)
):
    """Get room amenities"""
    return await AmenityServices.get_room_amenities(session, room_id)


@amenity_router.get("/", response_model=List[AmenityResponse], status_code=status.HTTP_200_OK)
async def get_amenities(
        amenity_type: Optional[AmenityType] = Query(None),
        session: AsyncSession = Depends(get_session),
):
    """Get amenities"""
    return await AmenityServices.get_all_amenities(session, amenity_type)


@amenity_router.post("/", response_model=AmenityResponse, status_code=status.HTTP_201_CREATED)
async def create_amenity(
        amenity_create: AmenityCreate,
        session: AsyncSession = Depends(get_session),
        admin: User = Depends(get_admin_user)
):
    """Create new amenity"""
    return await AmenityServices.create_amenity(session, amenity_create)


@amenity_router.put("/{amenity_id}", response_model=AmenityResponse, status_code=status.HTTP_202_ACCEPTED)
async def update_amenity(
        amenity_update: AmenityUpdate,
        amenity_id: int = Path(..., ge=1),
        session: AsyncSession = Depends(get_session),
        admin: User = Depends(get_admin_user)
):
    """Update amenity"""
    return await AmenityServices.update_amenity(session, amenity_update, amenity_id)


@property_amenity_router.put("/", response_model=List[AmenityResponse], status_code=status.HTTP_202_ACCEPTED)
async def update_property_amenities(
        amenity_data: AmenityAssign,
        property_id: int = Path(..., ge=1),
        session: AsyncSession = Depends(get_session),
        current_user: User = Depends(get_owner_or_admin_user)
):
    is_owner = await RoomService.check_user_is_owner_by_property(
        session=session,
        property_id=property_id,
        owner_id=current_user.user_id
    )

    if not is_owner or current_user.role != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to perform this action"
        )

    return await AmenityServices.update_property_amenities(
        session=session,
        property_id=property_id,
        amenity_ids=amenity_data.amenity_ids
    )


@room_amenity_router.put("/", response_model=List[AmenityResponse], status_code=status.HTTP_202_ACCEPTED)
async def update_room_amenities(
        amenity_data: AmenityAssign,
        room_id: int = Path(..., ge=1),
        session: AsyncSession = Depends(get_session),
        current_user: User = Depends(get_owner_or_admin_user)
):
    is_owner = await RoomService.check_user_is_owner_by_room(
        session=session,
        room_id=room_id,
        owner_id=current_user.user_id
    )

    if not is_owner or current_user.role != Role.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="You do not have permission to perform this action")

    return await AmenityServices.update_room_amenities(
        session=session,
        room_id=room_id,
        amenity_ids=amenity_data.amenity_ids
    )


@amenity_router.delete("/{amenity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_amenity(
        amenity_id: int = Path(..., ge=1),
        session: AsyncSession = Depends(get_session),
        admin: User = Depends(get_admin_user)
):
    """Delete amenity"""
    await AmenityServices.delete_amenity(session, amenity_id)
