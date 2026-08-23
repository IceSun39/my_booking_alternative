from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.services.search_servises import SearchServices
from src.backend.schemas.properties_schemas import PropertiesResponse
from src.backend.schemas.search_schemas import SearchFilter
from src.backend.database.database import get_session
from src.backend.core.dependencies import get_current_user, get_admin_user
from typing import List

search_router = APIRouter(
    prefix="/api/search",
    tags=["search"],
)
SearchServices = SearchServices()

@search_router.get("/", response_model=List[PropertiesResponse])
async def search_properties(
        filters: SearchFilter = Depends(),
        session: AsyncSession = Depends(get_session),
):
    return await SearchServices.find_available_properties(session, filters)

