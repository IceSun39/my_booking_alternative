from src.backend.models import User
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.services.rooms_services import RoomService
from src.backend.models import Role
from src.backend.schemas.rooms_schemas import RoomResponse, RoomCreate, RoomUpdate
from src.backend.database.database import get_session
from src.backend.core.dependencies import get_current_user, get_owner_or_admin_user

room_router = APIRouter(
    prefix="/api/rooms",
    tags=["Room"],
)

RoomService = RoomService()

async def check_user_is_room_owner(session: AsyncSession, room_id: int, current_user: User):
    is_owner = await RoomService.check_user_is_owner_by_room(
        session=session,
        room_id=room_id,
        owner_id=current_user.user_id
    )

    if not is_owner and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to perform this action"
        )

    return True

@room_router.get("/{room_id}", response_model=RoomResponse)
async def get_room(room_id: int, session: AsyncSession = Depends(get_session),
                   current_user: User = Depends(get_current_user)):
    return await RoomService.get_room(session=session, room_id=room_id)


@room_router.post("/", response_model=RoomResponse, status_code=status.HTTP_201_CREATED)
async def create_room(room: RoomCreate, session: AsyncSession = Depends(get_session),
                      current_user: User = Depends(get_owner_or_admin_user)):
    is_owner = await RoomService.check_user_is_owner_by_property(
        session=session,
        property_id=room.property_id,
        owner_id=current_user.user_id
    )

    if not is_owner and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to perform this action"
        )

    return await RoomService.create_room(session=session, room_create=room)


@room_router.put("/{room_id}", response_model=RoomResponse)
async def update_room(room: RoomUpdate, room_id: int, session: AsyncSession = Depends(get_session),
                      current_user: User = Depends(get_owner_or_admin_user)):
    if await check_user_is_room_owner(session=session, room_id=room_id, current_user=current_user):
        return await RoomService.update_room(session=session, room_update=room, room_id=room_id)
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You do not have permission to perform this action"
    )


@room_router.delete("/{room_id}")
async def delete_room(room_id: int, session: AsyncSession = Depends(get_session),
                      current_user: User = Depends(get_owner_or_admin_user)):
    if await check_user_is_room_owner(session=session, room_id=room_id, current_user=current_user):
        await RoomService.delete_room(session=session, room_id=room_id)
