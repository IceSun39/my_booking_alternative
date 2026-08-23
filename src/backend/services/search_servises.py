from backend.models import Property, Room, Booking
from sqlalchemy import select, and_, exists
from sqlalchemy.ext.asyncio import AsyncSession
from src.backend.schemas.search_schemas import SearchFilter, SortBy
from typing import List

class SearchServices:
    @staticmethod
    async def find_available_properties(
            session: AsyncSession,
            filters: SearchFilter,
    ) -> List[Property]:
        # Take all properties with all rooms
        stmt = select(Property).join(Property.rooms)

        # Filter by city
        stmt = stmt.where(Property.city.ilike(filters.city))

        # Filter by number of guests
        stmt = stmt.where(Room.capacity >= filters.guest)

        # Filter by price
        if filters.min_price:
            stmt = stmt.where(Room.price > filters.min_price)
        if filters.max_price:
            stmt = stmt.where(Room.price < filters.max_price)

        # Filter by amenities
        if filters.amenities:
            stmt = stmt.where(Room.amenities.in_(filters.amenities))

        overlapping_bookings = select(Booking.booking_id).where(
            and_(
                Booking.room_id == Room.room_id,
                Booking.check_in < filters.check_out,
                Booking.check_out > filters.check_in,
            )
        )

        stmt = stmt.where(~exists(overlapping_bookings))

        stmt = stmt.distinct()

        if filters.sort_by:
            sort_by = filters.sort_by
            if sort_by == SortBy.PRICE_ASC:
                stmt = stmt.order_by(Room.price.asc())
            elif sort_by == SortBy.PRICE_DESC:
                stmt = stmt.order_by(Room.price.desc())
            elif sort_by == SortBy.REVIEW_ASC:
                stmt = stmt.order_by(Property.rating.asc())
            elif sort_by == SortBy.REVIEW_DESC:
                stmt = stmt.order_by(Property.rating.desc())

        result = await session.execute(stmt)
        return result.scalars().all()