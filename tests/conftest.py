import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from src.backend.main import app
from src.backend.database.database import get_session, Base
from src.backend.models import Amenity, Booking, Favorite, Property, Review, Room, User
from src.backend.models.associations import property_amenities, room_amenities

SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine_test = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=NullPool,
)
TestingSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine_test, class_=AsyncSession)


async def override_get_session():
    async with TestingSessionLocal() as session:
        yield session


app.dependency_overrides[get_session] = override_get_session


@pytest.fixture(autouse=True)
async def setup_db():
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac