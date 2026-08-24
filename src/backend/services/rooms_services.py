from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi import HTTPException

from src.backend.models import Room, Property
from src.backend.schemas.rooms_schemas import RoomResponse, RoomCreate, RoomUpdate


class RoomService:
    async def _get_room_in_db(self, session: AsyncSession, room_id: int) -> Optional[Room]:
        stmt = select(Room).where(Room.room_id == room_id).options(selectinload(Room.amenities))
        result = await session.execute(stmt)
        room = result.scalar_one_or_none()

        if room is None:
            raise HTTPException(status_code=404, detail="Room not found")
        return room

    # Нехай буде якщо session.refresh не буде працювати
    async def _refresh_room_in_db(self, session: AsyncSession, room_id: int) -> Room:
        stmt = select(Room).where(Room.room_id == room_id).options(selectinload(Room.amenities))
        result = await session.execute(stmt)
        room = result.scalar_one_or_none()
        return room

    async def check_user_is_owner_by_room(self, session: AsyncSession, room_id:int, owner_id: int) -> bool:
        stmt = select(Property).join(Property.rooms).where(Room.room_id == room_id)
        result = await session.execute(stmt)
        property = result.scalar_one_or_none()

        if property is None:
            return False
        return property.owner_id == owner_id

    async def check_user_is_owner_by_property(self, session: AsyncSession, property_id: int, owner_id: int) -> bool:
        stmt = select(Property).where(Property.property_id == property_id)
        result = await session.execute(stmt)
        property = result.scalar_one_or_none()

        if property is None:
            return False
        return property.owner_id == owner_id

    async def get_room(self, session: AsyncSession, room_id: int) -> RoomResponse:
        existing_room = await self._get_room_in_db(session, room_id)
        return RoomResponse.model_validate(existing_room)

    async def create_room(self, session: AsyncSession, room_create: RoomCreate) -> RoomResponse:
        stmt = select(Room).where(Room.name == room_create.name, Room.property_id == room_create.property_id).options(selectinload(Room.amenities))
        result = await session.execute(stmt)
        existing_room = result.scalar_one_or_none()
        if existing_room:
            raise HTTPException(status_code=400, detail="Room already exists")

        room_data = room_create.model_dump()
        new_room = Room(
            **room_data
        )

        session.add(new_room)
        await session.flush()
        room_id = new_room.room_id
        await session.commit()
        new_room = await self._refresh_room_in_db(session=session, room_id=room_id)
        return RoomResponse.model_validate(new_room)

    async def update_room(self, session: AsyncSession, room_update: RoomUpdate, room_id: int) -> RoomResponse:
        existing_room = await self._get_room_in_db(session=session, room_id=room_id)

        update_data = room_update.model_dump(exclude_unset=True, exclude={"amenities","room_id"})

        for key, value in update_data.items():
            setattr(existing_room, key, value)

        await session.commit()
        existing_room = await self._refresh_room_in_db(session=session, room_id=room_id)
        return RoomResponse.model_validate(existing_room)

    async def delete_room(self, session: AsyncSession, room_id: int) -> None:
        existing_room = await self._get_room_in_db(session=session, room_id=room_id)

        await session.delete(existing_room)
        await session.commit()

        return None
