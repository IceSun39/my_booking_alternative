from typing import Optional, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from src.backend.models import Booking, Room, BookingStatus
from src.backend.schemas.bookings_schemas import BookingCreate, BookingUpdate, BookingResponse, BookingBase
from src.backend.services.rooms_services import RoomService
from datetime import date

room_service = RoomService()

# Bookings only with this statuses will be findings in database for
# checking date collisions
ACTIVE_BOOKING_STATUSES = {
    BookingStatus.PENDING,
    BookingStatus.CONFIRMED,
}

class BookingService:
    async def _get_booking_in_db(
            self,
            session: AsyncSession,
            booking_id: int
    ) -> Optional[Booking]:
        """Helper method for getting booking by id"""
        stmt = select(Booking).where(Booking.booking_id == booking_id)
        result = await session.execute(stmt)
        booking = result.scalar_one_or_none()

        if booking is None:
            raise HTTPException(status_code=404, detail="Booking not found")
        return booking

    async def _find_all_bookings_for_room(
            self,
            session: AsyncSession,
            room_id: int,
            check_in: date,
            check_out: date,
            exclude_booking_id: Optional[int] = None
    ) -> List[Booking]:
        """Method finds all bookings there cross dates"""
        # Basic statement
        stmt = select(Booking).where(
            Booking.room_id == room_id,
            check_in < Booking.check_out,
            check_out > Booking.check_in,
            Booking.status.in_(ACTIVE_BOOKING_STATUSES),
        )

        # Exclude booking if we're updating it
        if exclude_booking_id:
            stmt = stmt.where(Booking.booking_id != exclude_booking_id)

        stmt = stmt.order_by(Booking.check_in.asc())
        result = await session.execute(stmt)
        return result.scalars().all()

    async def _check_booking_dates_for_hostel_rooms(
            self,
            session: AsyncSession,
            booking: BookingBase,
            room: Room,
            exclude_booking_id: Optional[int] = None
    ) -> bool:
        """Method checks whether there are any available places in the room"""
        bookings = await self._find_all_bookings_for_room(session, room.room_id, booking.check_in, booking.check_out,
                                                          exclude_booking_id)

        # Nothing is gets in the way, if there are no bookings
        if not bookings:
            return True
        total_days = (booking.check_out - booking.check_in).days
        # Create a list of zeros whose length is equal to the number of days of stay
        guests_per_day = [0] * total_days

        for books in bookings:
            # Start Date: If they arrived before us, then for us they are counted starting on Day 0
            start_day = max(0, (books.check_in - booking.check_in).days)

            # Final Date: If they're leaving later than us, we'll cut it off at our last day
            end_day = min(total_days, (books.check_out - booking.check_in).days)

            # Add number of guests for every day
            for i in range(start_day, end_day):
                guests_per_day[i] += books.guests

        # Check if there's enough space for new guests on EVERY single day
        for current_guests in guests_per_day:
            if room.capacity - current_guests < booking.guests:
                return False  # Find day, when not enough space

        return True

    async def _check_booking_dates_for_hotel_rooms(
            self,
            session: AsyncSession,
            booking: BookingBase,
            room: Room,
            exclude_booking_id: Optional[int] = None
    ) -> bool:
        """Methods checks whether the room is available on the specified dates"""
        bookings = await self._find_all_bookings_for_room(session, room.room_id, booking.check_in, booking.check_out,
                                                          exclude_booking_id)

        if not bookings:
            return True

        return False

    async def _check_booking_available(
            self,
            session: AsyncSession,
            booking: BookingBase,
            room: Room,
            exclude_booking_id: Optional[int] = None
    ) -> bool:
        """Checks to see if the recording room is available"""

        if room.is_contains_several_groups:
            return await self._check_booking_dates_for_hostel_rooms(session, booking, room, exclude_booking_id)

        return await self._check_booking_dates_for_hotel_rooms(session, booking, room, exclude_booking_id)

    async def get_booking(
            self,
            session: AsyncSession,
            booking_id: int
    ) -> Optional[BookingResponse]:
        """Return booking response model by id"""
        booking = await self._get_booking_in_db(session, booking_id)
        return BookingResponse.model_validate(booking)

    async def get_all_user_bookings(
            self,
            session: AsyncSession,
            user_id: int
    ) -> List[BookingResponse]:
        """Return all user's bookings"""
        stmt = select(Booking).where(Booking.user_id == user_id)
        result = await session.execute(stmt)
        bookings = result.scalars().all()

        return [BookingResponse.model_validate(booking) for booking in bookings]

    async def create_booking(
            self,
            session: AsyncSession,
            booking_create: BookingCreate,
            user_id: int
    ) -> BookingResponse:
        """Create new booking"""
        room = await room_service._get_room_in_db(session, booking_create.room_id)

        # Check if room is available
        is_available = await self._check_booking_available(session, booking_create, room)

        if not is_available:
            raise HTTPException(
                status_code=400,
                detail="Not enough room available for these dates"
            )

        # Calculate the price
        total_price = room.price * (booking_create.check_out - booking_create.check_in).days
        booking_data = booking_create.model_dump()
        new_booking = Booking(
            **booking_data,
            total_price=total_price,
            user_id=user_id,
            status=BookingStatus.PENDING
        )

        try:
            session.add(new_booking)
            await session.commit()
            await session.refresh(new_booking)
            return BookingResponse.model_validate(new_booking)

        # If not enough room
        except IntegrityError as e:
            await session.rollback()

            if "exclude_overlapping_bookings" in str(e.orig):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="На жаль, ці дати щойно забронював хтось інший. Оберіть, будь ласка, інші дати."
                )
            raise e

    async def update_booking(
            self,
            session: AsyncSession,
            booking_update: BookingUpdate,
            booking_id: int
    ) -> Optional[BookingResponse]:
        """Updates booking by id"""
        existing_booking = await self._get_booking_in_db(session, booking_id)
        update_data = booking_update.model_dump(exclude_unset=True)

        check_in = update_data.get("check_in", existing_booking.check_in)
        check_out = update_data.get("check_out", existing_booking.check_out)
        guests = update_data.get("guests", existing_booking.guests)
        room_id = update_data.get("room_id", existing_booking.room_id)

        booking_to_check = BookingBase(check_in=check_in, check_out=check_out, guests=guests)
        room = await room_service._get_room_in_db(session, room_id)

        # Checking if is available
        is_available = await self._check_booking_available(session, booking_to_check, room,
                                                           exclude_booking_id=booking_id)

        if not is_available:
            raise HTTPException(
                status_code=400,
                detail="Not enough room available for these dates"
            )

        # If check in, check out date or room is changing, needs to recalculate the price
        if (check_in != existing_booking.check_in or
                check_out != existing_booking.check_out or
                room_id != existing_booking.room_id):
            total_price = room.price * (check_out - check_in).days
            existing_booking.total_price = total_price


        for key, value in update_data.items():
            setattr(existing_booking, key, value)

        await session.commit()
        await session.refresh(existing_booking)
        return BookingResponse.model_validate(existing_booking)

    async def delete_booking(
            self,
            session: AsyncSession,
            booking_id: int
    ) -> None:
        """Deletes booking by id"""
        booking = await self._get_booking_in_db(session, booking_id)

        await session.delete(booking)
        await session.commit()

        return None
