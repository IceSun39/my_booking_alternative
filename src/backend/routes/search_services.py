from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.database.database import get_session
from src.backend.schemas.properties_schemas import PropertiesResponse
from src.backend.schemas.search_schemas import SearchFilter
from src.backend.services.search_servises import SearchServices

search_router = APIRouter(
    prefix="/api/search",
    tags=["search"],
)
search_services = SearchServices()


@search_router.get("/", response_model=list[PropertiesResponse])
async def search_properties(
    filters: SearchFilter = Depends(),
    session: AsyncSession = Depends(get_session),
):
    return await search_services.find_available_properties(session, filters)
