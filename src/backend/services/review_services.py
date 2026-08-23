from typing import Optional, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from src.backend.models import Review, Booking, Property, Room
from src.backend.schemas.reviews_schemas import ReviewCreate, ReviewUpdate, ReviewResponse


class ReviewService:
    async def _get_reviews_in_db(self, session: AsyncSession, review_id: int) -> Optional[Review]:
        stmt = select(Review).where(Review.review_id == review_id)
        result = await session.execute(stmt)
        review = result.scalar_one_or_none()

        if review is None:
            raise HTTPException(status_code=404, detail="Review not found")
        return review

    async def _find_property(self, session: AsyncSession, booking_id: int) -> Property:
        stmt_prop = select(Property).join(Room).where(Property.property_id == Room.property_id)
        stmt_prop = stmt_prop.join(Booking).where(Booking.booking_id == booking_id)
        result = await session.execute(stmt_prop)
        property_obj = result.scalar_one_or_none()

        if property_obj is None:
            raise HTTPException(status_code=404, detail="Property not found")
        return property_obj

    async def get_property_reviews(self, session: AsyncSession, property_id: int) -> List[ReviewResponse]:
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

    async def create_review(self, session: AsyncSession, review_create: ReviewCreate, user_id: int, property_id: int) -> ReviewResponse:
        stmt = select(Review).where(Review.booking_id == review_create.booking_id)
        result = await session.execute(stmt)
        existing_review = result.scalar_one_or_none()
        if existing_review:
            raise HTTPException(status_code=400, detail="Review already exists")

        review_data = review_create.model_dump()
        new_review = Review(**review_data, user_id=user_id, property_id=property_id)

        session.add(new_review)

        property_obj = await self._find_property(session, review_create.booking_id)

        old_rating = property_obj.rating * property_obj.reviews_count
        new_rating = old_rating + review_create.rating
        property_obj.reviews_count += 1
        property_obj.rating = round(new_rating / property_obj.reviews_count, 2)

        await session.commit()
        await session.refresh(new_review)
        return ReviewResponse.model_validate(new_review)

    async def update_review(self, session: AsyncSession, review_update: ReviewUpdate, review_id: int) -> ReviewResponse:
        existing_review = await self._get_reviews_in_db(session=session, review_id=review_id)
        update_data = review_update.model_dump(exclude_unset=True)

        if "rating" in update_data and update_data["rating"] != existing_review.rating:
            old_review_rating = existing_review.rating
            new_review_rating = update_data["rating"]

            property_obj = await self._find_property(session, existing_review.booking_id)

            old_total = property_obj.rating * property_obj.reviews_count
            new_total = old_total - old_review_rating + new_review_rating
            property_obj.rating = round(new_total / property_obj.reviews_count, 2)

        for key, value in update_data.items():
            setattr(existing_review, key, value)

        await session.commit()
        await session.refresh(existing_review)
        return ReviewResponse.model_validate(existing_review)

    async def delete_review(self, session: AsyncSession, review_id: int) -> None:
        existing_review = await self._get_reviews_in_db(session=session, review_id=review_id)

        property_obj = await self._find_property(session, existing_review.booking_id)
        old_rating = property_obj.rating * property_obj.reviews_count
        new_rating = old_rating - existing_review.rating
        property_obj.reviews_count -= 1

        if property_obj.reviews_count > 0:
            property_obj.rating = round(new_rating / property_obj.reviews_count, 2)
        else:
            property_obj.rating = 0.0

        await session.delete(existing_review)
        await session.commit()

        return None
