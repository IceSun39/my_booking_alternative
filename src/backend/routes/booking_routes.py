from src.backend.models import Booking
from fastapi import APIRouter, Depends, status, Path, Body, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from src.backend.database.database import get_session
from src.backend.core.dependencies import get_current_user
from src.backend.models.users import User, Role
from src.backend.schemas.bookings_schemas import BookingCreate, BookingUpdate, BookingResponse
from src.backend.services.booking_services import BookingService

booking_router = APIRouter(
    prefix="/api/bookings",
    tags=["booking"],
)
BookingService = BookingService()


async def check_user_owner_booking(
        session: AsyncSession,
        booking_id: int,
        current_user: User
) -> bool:
    stmt = select(Booking.user_id).where(Booking.booking_id == booking_id)
    result = await session.execute(stmt)
    booking_owner_id = result.scalar_one_or_none()

    if booking_owner_id is None:
        raise HTTPException(status_code=404, detail="Booking not found")
    if current_user.user_id == booking_owner_id:
        return True
    return False


@booking_router.get("/my_bookings", response_model=List[BookingResponse], status_code=status.HTTP_200_OK)
async def my_bookings(
        current_user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_session)
):
    return await BookingService.get_all_user_bookings(session, current_user.user_id)


@booking_router.get("/{booking_id}", response_model=BookingResponse, status_code=status.HTTP_200_OK)
async def get_booking(
        booking_id: int = Path(..., ge=1),
        current_user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_session)
):
    is_owner = await check_user_owner_booking(session, booking_id, current_user)

    if is_owner or current_user.role == Role.ADMIN:
        return await BookingService.get_booking(session, booking_id)
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You do not have permission to perform this action"
    )


@booking_router.post("/", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def create_booking(
        booking_create: BookingCreate,
        session: AsyncSession = Depends(get_session),
        current_user: User = Depends(get_current_user)
):
    return await BookingService.create_booking(session, booking_create, current_user.user_id)


@booking_router.put("/{booking_id}", response_model=BookingResponse, status_code=status.HTTP_202_ACCEPTED)
async def update_booking(
        booking_id: int = Path(..., ge=1),
        booking_update: BookingUpdate = Body(...),
        session: AsyncSession = Depends(get_session),
        current_user: User = Depends(get_current_user)
):
    is_owner = await check_user_owner_booking(session, booking_id, current_user)

    if is_owner or current_user.role == Role.ADMIN:
        return await BookingService.update_booking(session, booking_update, booking_id)

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You do not have permission to perform this action"
    )


@booking_router.delete("/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_booking(
        booking_id: int = Path(..., ge=1),
        session: AsyncSession = Depends(get_session),
        current_user: User = Depends(get_current_user)
):
    is_owner = await check_user_owner_booking(session, booking_id, current_user)

    if is_owner or current_user.role == Role.ADMIN:
        await BookingService.delete_booking(session, booking_id)

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You do not have permission to perform this action"
    )
