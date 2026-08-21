from backend.models import Review
from backend.services.rooms_services import RoomService
from typing import Optional, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import selectinload, session

from src.backend.models import Booking, Room
from src.backend.schemas.booking_schemas import BookingCreate, BookingUpdate, BookingResponse, BookingBase
from src.backend.services.room_service import RoomService

RoomService = RoomService()


class BookingService():
    async def _get_booking_in_db(self, session: AsyncSession, booking_id: int) -> Optional[Booking]:
        """Метод знаходить бронювання по id"""
        stmt = select(Booking).where(Booking.id == booking_id)
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
            check_out > Booking.check_in
        ).order_by(Booking.check_in.asc())

        result = await session.execute(find_bookings)

        bookings = result.scalars().all()

        return bookings

    async def _check_booking_dates_for_hostel_rooms(self, session: AsyncSession, booking: BookingBase,
                                                    room: Room) -> bool:
        """Метод спершу рахує кількість гостей, які будуть у кімнаті в конкретні дати і потім перевіряє чи влазять туди нові гості"""
        bookings = await self._find_all_bookings_for_room(session, room.room_id, booking.check_in, booking.check_out)

        # Якщо записів немає, то нічого заважати і не може
        if bookings is None:
            return True
        total_days = (check_out - check_in).days
        guests = list(range(0, total_days))
        capacity, booking_guest = room.capacity, booking.guests

        # Головний цикл, рахуємо скільки кожного дня буде гостей
        for books in bookings:
            start_day = total_days - (check_out - books.check_in).days
            end_day = -(check_in - books.check_out).days
            end_day = end_day if end_day < total_days else total_days
            for i in range(start_day, end_day):
                guests[i] += books.guests

        # Якщо хоч в один день всі не влазять у кімнату, то місць немає
        for guest in guests:
            if capacity - guest <= booking_guest:
                return False
        return True

    # Метод перевіряє чи вільна кімната ГОТЕЛЮ
    async def _check_booking_dates_for_hotel_rooms(self, session: AsyncSession, booking: BookingBase,
                                                   room: Room) -> bool:
        """Метод перевіряє чи кімната пуста в задані дати"""
        bookings = await self._find_all_bookings_for_room(session, room.room_id, booking.check_in, booking.check_outz)

        # Якщо в кімнати взагалі немає записів, то ласкаво просимо
        if bookings is None:
            return True

        return False

    async def _check_booking_avaible(
            self,
            session: AsyncSession,
            booking: BookingBase,
            room: Room) -> bool:
        """Перевіряє чи вільна кімната для запису"""
        room = RoomService._get_room_in_db(session, room_id)
        # Якщо кімната типу хостела
        if room.is_contains_several_groups:
            return await self._check_booking_dates_for_hostel_rooms(session, booking, room)
        # Якщо кімната готельного типу
        return await self._check_booking_dates_for_hotel_rooms(session, booking, room)

    async def get_booking(self, session: AsyncSession, booking_id: int) -> Optional[BookingResponse]:
        booking = await self._get_booking_in_db(session, booking_id)
        return BookingResponse.model_validate(booking)

    async def create_booking(self, booking_create: BookingCreate) -> BookingResponse:
        room = RoomService._get_room_in_db(session, booking_create.room_id)

        if not self._check_booking_avaible(session, booking_create, room):
            return JSONResponse(content={
                "status": "error",
                "message": "Not enough room"
            })

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


        check_in = update_data["check_in"] if update_data["check_in"] else existing_booking.check_in
        check_out = update_data["check_out"] if update_data["check_out"] else existing_booking.check_out
        guests = update_data["guests"] if update_data["guests"] else existing_booking.guests
        room_id = update_data["room_id"] if update_data["room_id"] else existing_booking.room_id
        booking = BookingBase(check_in=check_in, check_out=check_out, guests=guests)
        room = RoomService._get_room_in_db(session, room_id)

        if not self._check_booking_avaible(session, booking, room):
            return JSONResponse(content={
                "status": "error",
                "message": "Not enough room"
            })

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

    
