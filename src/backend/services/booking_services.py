from typing import Optional, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from src.backend.models import Booking, Room
from src.backend.schemas.bookings_schemas import BookingCreate, BookingUpdate, BookingResponse, BookingBase
from src.backend.services.rooms_services import RoomService
from datetime import date

RoomService = RoomService()


class BookingService:
    async def _get_booking_in_db(self, session: AsyncSession, booking_id: int) -> Optional[Booking]:
        """Метод знаходить бронювання по id"""
        stmt = select(Booking).where(Booking.booking_id == booking_id)
        result = await session.execute(stmt)
        booking = result.scalar_one_or_none()

        if booking is None:
            raise HTTPException(status_code=404, detail="Booking not found")
        return booking

    async def _find_all_bookings_for_room(self, session: AsyncSession, room_id: int, check_in: date, check_out: date) -> \
            List[Booking]:
        """Метод знаходить всі бронювання, які перетинаються з нашими датами"""
        find_bookings = select(Booking).where(
            Booking.room_id == room_id,
            check_in < Booking.check_out,
            check_out > Booking.check_in,
            Booking.booking_id != Booking.booking_id
        ).order_by(Booking.check_in.asc())

        result = await session.execute(find_bookings)

        bookings = result.scalars().all()

        return bookings

    async def _check_booking_dates_for_hostel_rooms(self, session: AsyncSession, booking: BookingBase,
                                                    room: Room) -> bool:
        """Метод спершу рахує кількість гостей, які будуть у кімнаті в конкретні дати і потім перевіряє чи влазять туди нові гості"""
        bookings = await self._find_all_bookings_for_room(session, room.room_id, booking.check_in, booking.check_out)

        # Якщо записів немає, то нічого заважати і не може
        if not bookings:
            return True
        total_days = (booking.check_out - booking.check_in).days
        # Створюємо масив із нулів для кожного дня нашого проживання
        guests_per_day = [0] * total_days

        for books in bookings:
            # Індекс початку: якщо вони заїхали раніше за нас, то для нас вони є з 0-го дня
            start_day = max(0, (books.check_in - booking.check_in).days)

            # Індекс кінця: якщо вони виїжджають пізніше за нас, обрізаємо по наш останній день
            end_day = min(total_days, (books.check_out - booking.check_in).days)

            # Додаємо кількість гостей для кожного дня перетину
            for i in range(start_day, end_day):
                guests_per_day[i] += books.guests

        # Перевіряємо, чи вистачить місця для нових гостей у КОЖЕН із днів
        for current_guests in guests_per_day:
            if room.capacity - current_guests < booking.guests:
                return False  # Знайшли день, коли місць не вистачає

        return True

    # Метод перевіряє чи вільна кімната ГОТЕЛЮ
    async def _check_booking_dates_for_hotel_rooms(self, session: AsyncSession, booking: BookingBase,
                                                   room: Room) -> bool:
        """Метод перевіряє чи кімната пуста в задані дати"""
        bookings = await self._find_all_bookings_for_room(session, room.room_id, booking.check_in, booking.check_out)

        # Якщо в кімнати взагалі немає записів, то ласкаво просимо
        if not bookings:
            return True

        return False

    async def _check_booking_available(
            self,
            session: AsyncSession,
            booking: BookingBase,
            room: Room) -> bool:
        """Перевіряє чи вільна кімната для запису"""

        if room.is_contains_several_groups:
            return await self._check_booking_dates_for_hostel_rooms(session, booking, room)

        # Якщо кімната готельного типу
        return await self._check_booking_dates_for_hotel_rooms(session, booking, room)

    async def get_booking(self, session: AsyncSession, booking_id: int) -> Optional[BookingResponse]:
        booking = await self._get_booking_in_db(session, booking_id)
        return BookingResponse.model_validate(booking)

    async def create_booking(self, session: AsyncSession, booking_create: BookingCreate) -> BookingResponse:
        room = await RoomService._get_room_in_db(session, booking_create.room_id)

        is_available = await self._check_booking_available(session, booking_create, room)

        if not is_available:
            raise HTTPException(
                status_code=400,
                detail="Not enough room available for these dates"
            )

        booking_data = booking_create.model_dump()
        new_booking = Booking(**booking_data)

        session.add(new_booking)
        await session.commit()
        await session.refresh(new_booking)

        return BookingResponse.model_validate(new_booking)

    async def update_booking(self, session: AsyncSession, booking_update: BookingUpdate,
                             booking_id: int) -> Optional[BookingResponse]:
        existing_booking = await self._get_booking_in_db(session, booking_id)

        update_data = booking_update.model_dump(exclude_unset=True)

        check_in = update_data.get("check_in", existing_booking.check_in)
        check_out = update_data.get("check_out", existing_booking.check_out)
        guests = update_data.get("guests", existing_booking.guests)
        room_id = update_data.get("room_id", existing_booking.room_id)

        booking_to_check = BookingBase(check_in=check_in, check_out=check_out, guests=guests)

        room = await RoomService._get_room_in_db(session, room_id)

        is_available = await self._check_booking_available(session, booking_to_check, room)
        if not is_available:
            raise HTTPException(
                status_code=400,
                detail="Not enough room available for these dates"
            )

        for key, value in update_data.items():
            setattr(existing_booking, key, value)

        await session.commit()
        await session.refresh(existing_booking)
        return BookingResponse.model_validate(existing_booking)

    async def delete_booking(self, session: AsyncSession, booking_id: int) -> None:
        booking = await self._get_booking_in_db(session, booking_id)

        await session.delete(booking)
        await session.commit()

        return None
