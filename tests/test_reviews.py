import pytest
import datetime
from src.backend.models import RoomType
from httpx import AsyncClient
from sqlalchemy import select

from src.backend.main import app
from tests.conftest import TestingSessionLocal
from src.backend.models import User, Role, Property, Room, Booking, Review
from src.backend.models.bookings import BookingStatus
from src.backend.core.dependencies import get_current_user


@pytest.fixture
async def setup_review_data():
    async with TestingSessionLocal() as session:
        # 1. Юзери
        owner = User(email="owner_rev@test.com", password="pwd", username="owner", role=Role.OWNER)
        reviewer = User(email="reviewer@test.com", password="pwd", username="reviewer", role=Role.USER)
        other_user = User(email="other_rev@test.com", password="pwd", username="other", role=Role.USER)
        session.add_all([owner, reviewer, other_user])
        await session.flush()

        # Зберігаємо ID юзерів ДО commit!
        owner_id = owner.user_id
        reviewer_id = reviewer.user_id
        other_id = other_user.user_id

        # 2. Готель і кімната
        prop = Property(
            name="Rev Hotel",
            country="UA",
            city="Kyiv",
            street="A",
            house_number="1",
            description="Nice place",
            owner_id=owner_id,
            rating=4.0,
            reviews_count=1
        )
        session.add(prop)
        await session.flush()
        prop_id = prop.property_id

        room = Room(property_id=prop_id, name="Lux", capacity=2, price=100, room_type=RoomType.PRIVATE)
        session.add(room)
        await session.flush()
        room_id = room.room_id

        # 3. Бронювання
        past_booking = Booking(
            user_id=reviewer_id,
            room_id=room_id,
            check_in=datetime.date.today() - datetime.timedelta(days=10),
            check_out=datetime.date.today() - datetime.timedelta(days=5),
            guests=1,
            total_price=500,
            status=BookingStatus.COMPLETED
        )
        future_booking = Booking(
            user_id=reviewer_id,
            room_id=room_id,
            check_in=datetime.date.today() + datetime.timedelta(days=1),
            check_out=datetime.date.today() + datetime.timedelta(days=5),
            guests=1,
            total_price=400,
            status=BookingStatus.CONFIRMED
        )
        session.add_all([past_booking, future_booking])
        await session.flush()

        past_booking_id = past_booking.booking_id
        future_booking_id = future_booking.booking_id

        # 4. Відгук для минулого бронювання
        review = Review(
            user_id=reviewer_id,
            property_id=prop_id,
            booking_id=past_booking_id,
            rating=4,
            comment="Good!"
        )
        session.add(review)
        await session.flush()
        review_id = review.review_id

        # Фіксуємо транзакцію (всі ID уже збережені у змінних)
        await session.commit()

        return {
            "reviewer_id": reviewer_id,
            "other_id": other_id,
            "property_id": prop_id,
            "past_booking_id": past_booking_id,
            "future_booking_id": future_booking_id,
            "review_id": review_id
        }


@pytest.mark.asyncio
async def test_create_review_future_booking_fails(async_client: AsyncClient, setup_review_data):
    """Помилка 400: не можна залишити відгук до виїзду"""
    data = setup_review_data

    async def override_user():
        return User(user_id=data["reviewer_id"], email="reviewer@test.com", role=Role.USER)

    app.dependency_overrides[get_current_user] = override_user

    try:
        payload = {"booking_id": data["future_booking_id"], "rating": 5, "comment": "Great"}
        response = await async_client.post(f"/api/properties/{data['property_id']}/reviews/", json=payload)

        assert response.status_code == 400, f"Unexpected error: {response.json()}"
        assert "before check-out" in response.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_update_review_success_and_rating_math(async_client: AsyncClient, setup_review_data):
    """Тестуємо зміну відгуку і перерахунок рейтингу готелю"""
    data = setup_review_data

    async def override_user():
        return User(user_id=data["reviewer_id"], email="reviewer@test.com", role=Role.USER)

    app.dependency_overrides[get_current_user] = override_user

    try:
        # Змінюємо оцінку з 4 на 10
        payload = {"rating": 10, "comment": "Amazing!"}
        response = await async_client.put(f"/api/reviews/{data['review_id']}", json=payload)

        assert response.status_code == 200, f"Error updating review: {response.json()}"
        assert response.json()["rating"] == 10

        # Перевіряємо оновлений рейтинг готелю в БД
        async with TestingSessionLocal() as session:
            stmt = select(Property).where(Property.property_id == data["property_id"])
            prop = (await session.execute(stmt)).scalar_one()
            assert prop.rating == 10.0
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_update_review_forbidden(async_client: AsyncClient, setup_review_data):
    """Інший юзер не може змінити чужий відгук"""
    data = setup_review_data

    async def override_other_user():
        return User(user_id=data["other_id"], email="other_rev@test.com", role=Role.USER)

    app.dependency_overrides[get_current_user] = override_other_user

    try:
        payload = {"rating": 1}
        response = await async_client.put(f"/api/reviews/{data['review_id']}", json=payload)
        assert response.status_code == 403, f"Unexpected response: {response.json()}"
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_delete_review_success(async_client: AsyncClient, setup_review_data):
    """Видалення відгуку та скидання рейтингу готелю до 0.0"""
    data = setup_review_data

    async def override_user():
        return User(user_id=data["reviewer_id"], email="reviewer@test.com", role=Role.USER)

    app.dependency_overrides[get_current_user] = override_user

    try:
        response = await async_client.delete(f"/api/reviews/{data['review_id']}")
        assert response.status_code in [200, 204], f"Error deleting review: {response.text}"

        # Перевіряємо скидання рейтингу в БД
        async with TestingSessionLocal() as session:
            stmt = select(Property).where(Property.property_id == data["property_id"])
            prop = (await session.execute(stmt)).scalar_one()
            assert prop.rating == 0.0
            assert prop.reviews_count == 0
    finally:
        app.dependency_overrides.pop(get_current_user, None)