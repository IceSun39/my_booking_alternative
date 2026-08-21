from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from src.backend.models.properties import Property
from src.backend.schemas.properties_schemas import PropertiesCreate, PropertiesUpdate, PropertiesResponse


class PropertyService:
    async def _get_property_in_db(self, session: AsyncSession, property_id: int) -> Optional[Property]:
        stmt = select(Property).where(Property.property_id == property_id)
        result = await session.execute(stmt)
        property = result.scalar_one_or_none()

        if property is None:
            raise HTTPException(status_code=404, detail="Property not found")
        return property

    async def get_property(self, session: AsyncSession, property_id: int) -> PropertiesResponse:
        property = await self._get_property_in_db(session=session, property_id=property_id)
        return PropertiesResponse.model_validate(property)

    async def create_property(self, session: AsyncSession, properties_create: PropertiesCreate) -> PropertiesResponse:
        stmt = select(Property).where(Property.name == properties_create.name)
        result = await session.execute(stmt)
        property = result.scalar_one_or_none()
        if property:
            raise HTTPException(status_code=409, detail="Property with this name already exists")

        property_data = properties_create.model_dump()
        new_property = Property(**property_data)

        session.add(new_property)
        await session.commit()
        await session.refresh(new_property)
        return PropertiesResponse.model_validate(new_property)

    async def update_property(self, session: AsyncSession, properties_update: PropertiesUpdate, property_id: int) -> PropertiesResponse:
        existing_property = await self._get_property_in_db(session=session, property_id=property_id)

        update_data = properties_update.model_dump(exclude_unset=True)

        for key, value in update_data.items():
            setattr(existing_property, key, value)

        await session.commit()
        await session.refresh(existing_property)
        return PropertiesResponse.model_validate(existing_property)

    async def delete_property(self, session: AsyncSession, property_id: int) -> None:
        existing_property = await self._get_property_in_db(session=session, property_id=property_id)

        await session.delete(existing_property)
        await session.commit()

        return None
