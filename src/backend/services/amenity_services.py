from fastapi import HTTPException
from typing import Optional, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.backend.models.amenities import Amenity
from src.backend.schemas.amenities_schemas import AmenityResponse, AmenityCreate, AmenityUpdate

class AmenityServices:
    async def _get_amenity_in_db(self, session: AsyncSession, amenity_id: int) -> Optional[Amenity]:
        stmt = select(Amenity).where(Amenity.amenity_id == amenity_id).options(selectinload(Amenity.rooms),selectinload(Amenity.properties))
        result = await session.execute(stmt)
        amenity = result.scalar_one_or_none()

        if amenity is None:
            raise HTTPException(status_code=404, detail="Amenity not found")
        return amenity

    async def create_amenity(self,session: AsyncSession, amenity_create: AmenityCreate) -> AmenityResponse:
        stmt = select(Amenity).where(Amenity.name == amenity_create.name).options(selectinload(Amenity.rooms), selectinload(Amenity.properties))
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

    async def update_amenity(self, session: AsyncSession, amenity_update: AmenityUpdate, amenity_id: int) -> AmenityResponse:
        existing_amenity = self._get_amenity_in_db(session=session, amenity_id=amenity_id)

        update_data = amenity_update.model_dump(exclude_unset=True)

        for key, value in update_data.items():
            setattr(existing_amenity, key, value)

        await session.commit()
        await session.refresh(existing_amenity)
        return AmenityResponse.model_validate(existing_amenity)

    async def delete_amenity(self, session: AsyncSession, amenity_id: int) -> None:
        existing_amenity = self._get_amenity_in_db(session=session, amenity_id=amenity_id)

        await session.delete(existing_amenity)
        await session.commit()

        return None
