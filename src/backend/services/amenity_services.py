from fastapi import HTTPException
from typing import Optional, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.backend.models import Amenity, Property, Room, AmenityType
from src.backend.schemas.amenities_schemas import AmenityResponse, AmenityCreate, AmenityUpdate


class AmenityServices:
    async def _get_amenity_in_db(
            self,
            session: AsyncSession,
            amenity_id: int
    ) -> Optional[Amenity]:
        """Helper method to get amenity item by id"""
        stmt = select(Amenity).where(Amenity.amenity_id == amenity_id).options(selectinload(Amenity.rooms),
                                                                               selectinload(Amenity.properties))
        result = await session.execute(stmt)
        amenity = result.scalar_one_or_none()

        if amenity is None:
            raise HTTPException(status_code=404, detail="Amenity not found")
        return amenity

    async def get_property_amenities(
            self,
            session: AsyncSession,
            property_id: int
    ) -> List[AmenityResponse]:
        """Get all amenities associated with a property"""
        stmt = select(Amenity).join(Amenity.properties).where(Property.property_id == property_id)
        result = await session.execute(stmt)
        amenities = result.scalars().all()

        return [AmenityResponse.model_validate(amenity) for amenity in amenities]

    async def get_room_amenities(
            self,
            session: AsyncSession,
            room_id: int
    ) -> List[AmenityResponse]:
        """Get all amenities associated with a room"""
        stmt = select(Amenity).join(Amenity.rooms).where(Room.room_id == room_id).options(selectinload(Room.amenities))
        result = await session.execute(stmt)
        amenities = result.scalars().all()

        return [AmenityResponse.model_validate(amenity) for amenity in amenities]

    async def get_all_amenities(
            self,
            session: AsyncSession,
            amenity_type: Optional[AmenityType] = None
    ) -> List[AmenityResponse]:
        """Get all amenities"""
        stmt = select(Amenity).options(selectinload(Amenity.properties))

        if amenity_type:
            stmt = stmt.where(Amenity.type._in([amenity_type, AmenityType.BOTH]))

        result = await session.execute(stmt)
        amenities = result.scalars().all()
        return [AmenityResponse.model_validate(amenity) for amenity in amenities]

    async def create_amenity(
            self,
            session: AsyncSession,
            amenity_create: AmenityCreate
    ) -> AmenityResponse:
        """Create an amenity so that the owner can select from a drop-down list"""
        stmt = select(Amenity).where(Amenity.name == amenity_create.name).options(selectinload(Amenity.rooms),
                                                                                  selectinload(Amenity.properties))
        result = await session.execute(stmt)
        amenity = result.scalar_one_or_none()
        if amenity:
            raise HTTPException(status_code=400, detail="Amenity already exists")

        amenity_data = amenity_create.model_dump()
        new_amenity = Amenity(
            **amenity_data
        )

        session.add(new_amenity)
        await session.commit()
        await session.refresh(new_amenity)
        return AmenityResponse.model_validate(new_amenity)

    async def update_amenity(
            self,
            session: AsyncSession,
            amenity_update: AmenityUpdate,
            amenity_id: int
    ) -> AmenityResponse:
        """Update amenity"""
        existing_amenity = await self._get_amenity_in_db(session=session, amenity_id=amenity_id)

        update_data = amenity_update.model_dump(exclude_unset=True)

        for key, value in update_data.items():
            setattr(existing_amenity, key, value)

        await session.commit()
        await session.refresh(existing_amenity)
        return AmenityResponse.model_validate(existing_amenity)

    async def update_property_amenities(
            self,
            property_id,
            amenity_ids: List[int],
            session: AsyncSession
    ) -> List[AmenityResponse]:
        """Update amenities for a property"""
        stmt_prop = select(Property).where(Property.property_id == property_id).options(
            selectinload(Property.amenities))
        result_prop = await session.execute(stmt_prop)
        property_obj = result_prop.scalar_one_or_none()

        if property_obj is None:
            raise HTTPException(status_code=404, detail="Property does not exist")

        new_amenities = []
        if amenity_ids:
            stmt_am = select(Amenity).where(
                Amenity.amenity_id._in(amenity_ids),
                Amenity.type._in([AmenityType.PROPERTY, AmenityType.BOTH]),
            ).options(selectinload(Amenity.properties))

            result_am = await session.execute(stmt_am)
            new_amenities = result_am.scalars().all()

            if len(new_amenities) != len(amenity_ids):
                raise HTTPException(status_code=404, detail="Some amenities do not exist")

        property_obj.amenities = new_amenities
        await session.commit()

        return [AmenityResponse.model_validate(amenity) for amenity in new_amenities]

    async def update_room_amenities(
            self,
            room_id,
            amenity_ids: List[int],
            session: AsyncSession
    ) -> List[AmenityResponse]:
        """Update amenities for a room"""
        stmt_room = select(Room).where(Room.room_id == room_id).options(selectinload(Room.amenities))
        result_room = await session.execute(stmt_room)
        room_obj = result_room.scalar_one_or_none()

        if room_obj is None:
            raise HTTPException(status_code=404, detail="Room does not exist")

        new_amenities = []
        if amenity_ids:
            stmt_am = select(Amenity).where(
                Amenity.amenity_id._in(amenity_ids),
                Amenity.type._in([AmenityType.ROOM, AmenityType.BOTH]),
            ).options(selectinload(Amenity.properties))

            result_am = await session.execute(stmt_am)
            new_amenities = result_am.scalars().all()
            if len(new_amenities) != len(amenity_ids):
                raise HTTPException(status_code=404, detail="Some amenities do not exist")

        room_obj.amenities = new_amenities
        await session.commit()

        return [AmenityResponse.model_validate(amenity) for amenity in new_amenities]

    async def delete_amenity(
            self,
            session: AsyncSession,
            amenity_id: int
    ) -> None:
        """Delete amenity"""
        existing_amenity = await self._get_amenity_in_db(session=session, amenity_id=amenity_id)

        await session.delete(existing_amenity)
        await session.commit()

        return None
