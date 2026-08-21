from typing import Optional, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from sqlalchemy.orm import selectinload

from src.backend.models.rooms import Room
from src.backend.schemas.rooms_schemas import RoomResponse, RoomCreate, RoomUpdate


class RoomService:
    async def _get_room_in_db(self, session: AsyncSession, room_id: int) -> Optional[Room]:
        stmt = select(Room).where(Room.id == room_id)
        result = await session.execute(stmt)
        room = result.scalar_one_or_none()

        if room is None:
            raise HTTPException(status_code=404, detail="Room not found")
        return room

    async def get_room(self, session: AsyncSession, room_id: int) -> RoomResponse:
        existing_room = await self._get_room_in_db(room_id)
        return RoomResponse.model_validate(existing_room)

    async def create_room(self, session: AsyncSession, room_create: RoomCreate) -> RoomResponse:
        existing_room = await self._get_room_in_db(room.id)
        if existing_room:
            raise HTTPException(status_code=400, detail="Room already exists")

        room_data = room_create.model_dump()
        new_room = Room(
            **room_data
        )

        session.add(new_room)
        await session.commit()
        await session.refresh(new_room)
        return RoomResponse.model_validate(new_room)

    async def update_room(self, session: AsyncSession, room_update: RoomUpdate) -> RoomResponse:
        existing_room = await self._get_room_in_db(room_update.id)

        update_data = room_update.model_dump(exclude_unset=True)

        for key, value in update_data.items():
            setattr(existing_room, key, value)

        await session.commit()
        await session.refresh(existing_room)
        return RoomResponse.model_validate(existing_room)

    async def delete_room(self, session: AsyncSession, room_id: int) -> None:
        existing_room = await self._get_room_in_db(room_id)

        await session.delete(existing_room)
        await session.commit()

        return None
