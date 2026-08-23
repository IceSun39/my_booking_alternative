import datetime

from src.backend.models import User
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.services import ReviewService, BookingService
from src.backend.schemas.reviews_schemas import ReviewUpdate, ReviewCreate, ReviewResponse
from src.backend.database.database import get_session
from src.backend.core.dependencies import get_current_user
from typing import List

review_property_router = APIRouter(
    prefix="/api/properties/{property_id}/reviews",
    tags=["reviews"],
)
review_router = APIRouter(
    prefix="/api/reviews",
    tags=["reviews"],
)
ReviewService = ReviewService()
BookingService = BookingService()


async def check_is_user_review_owner(
        review_id: int,
        user: User,
        session: AsyncSession = Depends(get_session)
) -> bool:
    review = await ReviewService.get_review(session=session, review_id=review_id)

    if review.user_id != user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can change reviews for your own bookings"
        )

    return True


@review_property_router.get("/", response_model=List[ReviewResponse])
async def get_property_reviews(
        property_id: int,
        session: AsyncSession = Depends(get_session),
        current_user: User = Depends(get_current_user)
):
    return await ReviewService.get_property_reviews(session, property_id)


@review_property_router.get("/{room_id}", response_model=List[ReviewResponse])
async def get_room_review(
        room_id: int,
        session: AsyncSession = Depends(get_session),
        current_user: User = Depends(get_current_user)
):
    return await ReviewService.get_room_reviews(session, room_id)


@review_property_router.post("/", response_model=ReviewResponse)
async def create_property_review(
        property_id: int,
        review_create: ReviewCreate,
        session: AsyncSession = Depends(get_session),
        current_user: User = Depends(get_current_user)
):
    booking = await BookingService.get_booking(session=session, booking_id=review_create.booking_id)

    if booking.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only leave reviews for your own bookings"
        )

    if booking.check_out > datetime.now().date():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You can't review a booking before check-out"
        )

    review_create.user_id = current_user.user_id
    review_create.property_id = property_id

    return await ReviewService.create_review(session=session, review_create=review_create)


@review_router.put("/{review_id}", response_model=ReviewResponse)
async def update_review(
        review_id: int,
        review_update: ReviewUpdate,
        session: AsyncSession = Depends(get_session),
        current_user: User = Depends(get_current_user)
):
    if await check_is_user_review_owner(review_id=review_id, user=current_user):
        return await ReviewService.update_review(session=session, review_update=review_update, review_id=review_id)
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You can change reviews for your own bookings"
    )


@review_router.delete("/{review_id}")
async def delete_review(
        review_id: int,
        session: AsyncSession = Depends(get_session),
        current_user: User = Depends(get_current_user)
):
    if await check_is_user_review_owner(review_id=review_id, user=current_user):
        await ReviewService.delete_review(session=session, review_id=review_id)
