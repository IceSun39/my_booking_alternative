import datetime
import pytest

from tests.conftest import TestingSessionLocal
from src.backend.models import Property, Room, Booking, Amenity, User, Role, RoomType
from src.backend.models.amenities import AmenityType
from src.backend.models.associations import room_amenities
from src.backend.models.bookings import BookingStatus
from src.backend.services.search_servises import SearchServices
from src.backend.schemas.search_schemas import SearchFilter, SortBy


@pytest.fixture
async def setup_search_data():
    async with TestingSessionLocal() as session:
        owner = User(email="owner_search@test.com", password="pwd", username="owner", role=Role.OWNER)
        session.add(owner)
        await session.flush()
        owner_id = owner.user_id

        wifi = Amenity(name="WiFi", type=AmenityType.ROOM)
        pool = Amenity(name="Pool", type=AmenityType.ROOM)
        session.add_all([wifi, pool])
        await session.flush()
        wifi_id, pool_id = wifi.amenity_id, pool.amenity_id

        # Property A — Kyiv, дешева кімната на 2, WiFi, є перекриваюче бронювання
        prop_a = Property(
            name="A", country="UA", city="Kyiv", street="A", house_number="1",
            description="d", owner_id=owner_id, rating=4.0, reviews_count=1
        )
        # Property B — Kyiv, дорожча кімната на 4, WiFi+Pool, без бронювань
        prop_b = Property(
            name="B", country="UA", city="Kyiv", street="B", house_number="2",
            description="d", owner_id=owner_id, rating=2.0, reviews_count=1
        )
        # Property C — Lviv, кімната на 2, без amenities
        prop_c = Property(
            name="C", country="UA", city="Lviv", street="C", house_number="3",
            description="d", owner_id=owner_id, rating=3.0, reviews_count=1
        )
        session.add_all([prop_a, prop_b, prop_c])
        await session.flush()
        property_a_id = prop_a.property_id
        property_b_id = prop_b.property_id
        property_c_id = prop_c.property_id

        room_a = Room(property_id=prop_a.property_id, name="A1", capacity=2, price=100, room_type=RoomType.PRIVATE)
        room_b = Room(property_id=prop_b.property_id, name="B1", capacity=4, price=200, room_type=RoomType.PRIVATE)
        room_c = Room(property_id=prop_c.property_id, name="C1", capacity=2, price=80, room_type=RoomType.PRIVATE)
        session.add_all([room_a, room_b, room_c])
        await session.flush()

        await session.execute(
            room_amenities.insert().values(
                [
                    {"room_id": room_a.room_id, "amenity_id": wifi_id},
                    {"room_id": room_b.room_id, "amenity_id": wifi_id},
                    {"room_id": room_b.room_id, "amenity_id": pool_id},
                ]
            )
        )

        # Бронювання на Room A, що перекриває шуканий діапазон 2026-09-10..2026-09-15
        overlapping_booking = Booking(
            user_id=owner_id,
            room_id=room_a.room_id,
            check_in=datetime.date(2026, 9, 12),
            check_out=datetime.date(2026, 9, 20),
            guests=1,
            total_price=500,
            status=BookingStatus.CONFIRMED,
        )
        # Бронювання на Room B, що НЕ перекриває шуканий діапазон
        non_overlapping_booking = Booking(
            user_id=owner_id,
            room_id=room_b.room_id,
            check_in=datetime.date(2026, 1, 1),
            check_out=datetime.date(2026, 1, 5),
            guests=1,
            total_price=500,
            status=BookingStatus.COMPLETED,
        )
        session.add_all([overlapping_booking, non_overlapping_booking])

        await session.commit()

        return {
            "property_a_id": property_a_id,
            "property_b_id": property_b_id,
            "property_c_id": property_c_id,
            "wifi_id": wifi_id,
            "pool_id": pool_id,
        }


def base_filters(**overrides) -> SearchFilter:
    defaults = dict(
        check_in=datetime.date(2026, 9, 10),
        check_out=datetime.date(2026, 9, 15),
        city="Kyiv",
        guest=1,
        min_price=None,
        max_price=None,
        amenities=None,
        sort_by=None,
    )
    defaults.update(overrides)
    return SearchFilter(**defaults)


@pytest.mark.asyncio
async def test_search_filters_by_city(setup_search_data):
    data = setup_search_data
    async with TestingSessionLocal() as session:
        results = await SearchServices.find_available_properties(session, base_filters(city="Lviv"))
        ids = {p.property_id for p in results}
        assert ids == {data["property_c_id"]}


@pytest.mark.asyncio
async def test_search_excludes_rooms_below_capacity(setup_search_data):
    data = setup_search_data
    async with TestingSessionLocal() as session:
        # Property A має кімнату на 2 місця, шукаємо на 3 — не має підійти
        filters = base_filters(city="Kyiv", guest=3)
        results = await SearchServices.find_available_properties(session, filters)
        ids = {p.property_id for p in results}
        assert data["property_a_id"] not in ids
        assert data["property_b_id"] in ids  # Room B на 4 місця підходить


@pytest.mark.asyncio
async def test_search_excludes_property_with_overlapping_booking(setup_search_data):
    data = setup_search_data
    async with TestingSessionLocal() as session:
        filters = base_filters(city="Kyiv", guest=1)
        results = await SearchServices.find_available_properties(session, filters)
        ids = {p.property_id for p in results}
        # Room A заброньована саме на ці дати — Property A не має з'явитись
        assert data["property_a_id"] not in ids
        # Room B вільна на ці дати (бронювання в іншому діапазоні)
        assert data["property_b_id"] in ids


@pytest.mark.asyncio
async def test_search_includes_property_when_dates_dont_overlap(setup_search_data):
    data = setup_search_data
    async with TestingSessionLocal() as session:
        # Шукаємо на дати ПІСЛЯ бронювання Room A — тепер Property A має бути доступна
        filters = base_filters(
            city="Kyiv",
            check_in=datetime.date(2026, 10, 1),
            check_out=datetime.date(2026, 10, 5),
        )
        results = await SearchServices.find_available_properties(session, filters)
        ids = {p.property_id for p in results}
        assert data["property_a_id"] in ids


@pytest.mark.asyncio
async def test_search_price_range_is_inclusive(setup_search_data):
    """Room A коштує рівно 100 — при min_price=100 має потрапити у видачу."""
    data = setup_search_data
    async with TestingSessionLocal() as session:
        filters = base_filters(
            city="Kyiv",
            check_in=datetime.date(2026, 11, 1),
            check_out=datetime.date(2026, 11, 5),
            min_price=100,
            max_price=100,
        )
        results = await SearchServices.find_available_properties(session, filters)
        ids = {p.property_id for p in results}
        assert data["property_a_id"] in ids
        assert data["property_b_id"] not in ids  # Room B коштує 200, поза межами


@pytest.mark.asyncio
async def test_search_filters_by_amenity(setup_search_data):
    """Фільтр по pool має повернути тільки Property B (єдина з Pool)."""
    data = setup_search_data
    async with TestingSessionLocal() as session:
        filters = base_filters(city="Kyiv", amenities=[data["pool_id"]])
        results = await SearchServices.find_available_properties(session, filters)
        ids = {p.property_id for p in results}
        assert ids == {data["property_b_id"]}


@pytest.mark.asyncio
async def test_search_amenity_shared_by_multiple_properties(setup_search_data):
    """WiFi є і в A, і в B — фільтр по WiFi має повернути обидві (A виключиться окремо через бронювання)."""
    data = setup_search_data
    async with TestingSessionLocal() as session:
        filters = base_filters(
            city="Kyiv",
            check_in=datetime.date(2026, 12, 1),
            check_out=datetime.date(2026, 12, 5),
            amenities=[data["wifi_id"]],
        )
        results = await SearchServices.find_available_properties(session, filters)
        ids = {p.property_id for p in results}
        assert ids == {data["property_a_id"], data["property_b_id"]}


@pytest.mark.asyncio
async def test_search_sort_by_review_desc(setup_search_data):
    data = setup_search_data
    async with TestingSessionLocal() as session:
        filters = base_filters(city="Kyiv", sort_by=SortBy.REVIEW_DESC)
        results = await SearchServices.find_available_properties(session, filters)
        ratings = [p.rating for p in results]
        assert ratings == sorted(ratings, reverse=True)


@pytest.mark.asyncio
async def test_search_sort_by_review_asc(setup_search_data):
    data = setup_search_data
    async with TestingSessionLocal() as session:
        filters = base_filters(city="Kyiv", sort_by=SortBy.REVIEW_ASC)
        results = await SearchServices.find_available_properties(session, filters)
        ratings = [p.rating for p in results]
        assert ratings == sorted(ratings)


@pytest.mark.asyncio
async def test_search_returns_no_duplicate_properties(setup_search_data):
    """Кожна Property має з'являтись рівно один раз, навіть якщо кілька її кімнат підходять."""
    async with TestingSessionLocal() as session:
        filters = base_filters(city="Kyiv")
        results = await SearchServices.find_available_properties(session, filters)
        ids = [p.property_id for p in results]
        assert len(ids) == len(set(ids))


@pytest.mark.asyncio
async def test_search_no_results_for_unknown_city(setup_search_data):
    async with TestingSessionLocal() as session:
        filters = base_filters(city="Odesa")
        results = await SearchServices.find_available_properties(session, filters)
        assert results == []