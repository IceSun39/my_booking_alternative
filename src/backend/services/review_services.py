from typing import Optional, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from src.backend.models import Review, Booking
from src.backend.schemas.reviews_schemas import ReviewCreate, ReviewUpdate, ReviewResponse


class ReviewService:
    async def _get_reviews_in_db(self, session: AsyncSession, review_id: int) -> Optional[Review]:
        stmt = select(Review).where(Review.review_id == review_id)
        result = await session.execute(stmt)
        review = result.scalar_one_or_none()

        if review is None:
            raise HTTPException(status_code=404, detail="Review not found")
        return review

    async def get_property_reviews(self, session: AsyncSession, property_id:int) -> List[ReviewResponse]:
        stmt = select(Review).where(Review.property_id == property_id)
        result = await session.execute(stmt)
        reviews = result.scalars().all()

        return [ReviewResponse.model_validate(review) for review in reviews]


    async def get_room_reviews(self, session: AsyncSession, room_id: int) -> List[ReviewResponse]:
        stmt = select(Review).join(Booking).where(Booking.room_id == room_id)
        result = await session.execute(stmt)
        reviews = result.scalars().all()

        return [ReviewResponse.model_validate(review) for review in reviews]

    async def get_review(self, session: AsyncSession, review_id: int) -> ReviewResponse:
        existing_review = await self._get_reviews_in_db(session, review_id)
        return ReviewResponse.model_validate(existing_review)

    async def create_review(self, session: AsyncSession, review_create: ReviewCreate) -> ReviewResponse:
        stmt = select(Review).where(Review.booking_id == review_create.booking_id)
        result = await session.execute(stmt)
        existing_review = result.scalar_one_or_none()
        if existing_review:
            raise HTTPException(status_code=400, detail="Review already exists")

        review_data = review_create.model_dump()
        new_review = Review(**review_data)

        session.add(new_review)
        await session.commit()
        await session.refresh(new_review)
        return ReviewResponse.model_validate(new_review)

    async def update_review(self, session: AsyncSession, review_update: ReviewUpdate, review_id: int) -> ReviewResponse:
        existing_review = await self._get_reviews_in_db(session=session, review_id=review_id)

        update_data = review_update.model_dump(exclude_unset=True)

        for key, value in update_data.items():
            setattr(existing_review, key, value)

        await session.commit()
        await session.refresh(existing_review)
        return ReviewResponse.model_validate(existing_review)

    async def delete_review(self, session: AsyncSession, review_id: int) -> None:
        existing_review = await self._get_reviews_in_db(session=session, review_id=review_id)

        await session.delete(existing_review)
        await session.commit()

        return None
