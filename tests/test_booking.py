import pytest
from httpx import AsyncClient
from datetime import date, timedelta
from src.backend.main import app
from tests.conftest import TestingSessionLocal
from src.backend.models import User, Role, Property, Room, Booking
from src.backend.models.bookings import BookingStatus
from src.backend.core.dependencies import get_current_user


@pytest.fixture
async def setup_booking_data():
    """Створюємо базові дані для тестів: юзера, готель і кімнату"""
    async with TestingSessionLocal() as session:
        # 1. Тестові користувачі
        user = User(email="guest@test.com", password="hashed_password", username="guest", role=Role.USER)
        other_user = User(email="other@test.com", password="hashed_password", username="other", role=Role.USER)
        admin = User(email="admin@test.com", password="hashed_password", username="admin", role=Role.ADMIN)

        session.add_all([user, other_user, admin])

        # ВИКОРИСТОВУЄМО FLUSH! Він генерує ID, але не експірує об'єкти.
        await session.flush()

        # Зберігаємо ID користувачів
        user_id = user.user_id
        other_user_id = other_user.user_id
        admin_id = admin.user_id

        # 2. Готель
        property_obj = Property(
            name="Test Hotel",
            country="Україна",
            city="Київ",
            street="Тестова",
            house_number="1",
            owner_id=user_id
        )
        session.add(property_obj)
        await session.flush()

        property_id = property_obj.property_id

        # 3. Кімнати
        room = Room(
            property_id=property_id,
            name="Standard Room",
            capacity=2,
            price=1000,
            is_contains_several_groups=False
        )
        hostel_room = Room(
            property_id=property_id,
            name="Hostel Bed",
            capacity=4,
            price=300,
            is_contains_several_groups=True
        )
        session.add_all([room, hostel_room])

        await session.flush()

        # Зберігаємо ID кімнат
        room_id = room.room_id
        hostel_room_id = hostel_room.room_id

        # Тепер, коли всі ID надійно збережені в змінні, комітимо все разом!
        await session.commit()

        return {
            "user_id": user_id,
            "other_user_id": other_user_id,
            "admin_id": admin_id,
            "room_id": room_id,
            "hostel_room_id": hostel_room_id
        }


@pytest.mark.asyncio
async def test_create_booking_success(async_client: AsyncClient, setup_booking_data):
    """Тестуємо успішне створення бронювання"""
    data = setup_booking_data

    # Авторизуємось як звичайний користувач
    async def override_get_current_user():
        return User(user_id=data["user_id"], email="guest@test.com", role=Role.USER)

    app.dependency_overrides[get_current_user] = override_get_current_user

    today = date.today()
    payload = {
        "check_in": str(today + timedelta(days=1)),
        "check_out": str(today + timedelta(days=5)),
        "guests": 2,
        "room_id": data["room_id"]
    }

    response = await async_client.post("/api/bookings/", json=payload)

    assert response.status_code == 201
    res_data = response.json()
    assert res_data["user_id"] == data["user_id"]
    assert res_data["room_id"] == data["room_id"]
    assert res_data["total_price"] == 4000  # 4 дні * 1000
    assert "booking_id" in res_data

    app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_create_booking_room_conflict(async_client: AsyncClient, setup_booking_data):
    """Тестуємо конфлікт дат (кімната вже зайнята)"""
    data = setup_booking_data

    async def override_get_current_user():
        return User(user_id=data["user_id"], email="guest@test.com", role=Role.USER)

    app.dependency_overrides[get_current_user] = override_get_current_user

    today = date.today()
    payload = {
        "check_in": str(today + timedelta(days=1)),
        "check_out": str(today + timedelta(days=5)),
        "guests": 1,
        "room_id": data["room_id"]
    }

    # Перше бронювання має пройти успішно
    resp1 = await async_client.post("/api/bookings/", json=payload)
    assert resp1.status_code == 201

    # Друге бронювання на ті самі дати має отримати помилку 400
    resp2 = await async_client.post("/api/bookings/", json=payload)
    assert resp2.status_code == 400
    assert resp2.json()["detail"] == "Not enough room available for these dates"

    app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_get_my_bookings(async_client: AsyncClient, setup_booking_data):
    """Тестуємо отримання списку бронювань поточного юзера"""
    data = setup_booking_data

    async def override_get_current_user():
        return User(user_id=data["user_id"], email="guest@test.com", role=Role.USER)

    app.dependency_overrides[get_current_user] = override_get_current_user

    # Створюємо бронювання
    today = date.today()
    await async_client.post("/api/bookings/", json={
        "check_in": str(today + timedelta(days=10)),
        "check_out": str(today + timedelta(days=12)),
        "guests": 1,
        "room_id": data["room_id"]
    })

    response = await async_client.get("/api/bookings/my_bookings")
    assert response.status_code == 200
    bookings_list = response.json()
    assert len(bookings_list) >= 1
    assert bookings_list[0]["user_id"] == data["user_id"]

    app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_booking_permissions_security(async_client: AsyncClient, setup_booking_data):
    """Тестуємо безпеку: чужий юзер не може переглядати/змінювати чуже бронювання, а адмін може"""
    data = setup_booking_data

    # 1. Створюємо бронювання від імені першого юзера
    async def override_user_1():
        return User(user_id=data["user_id"], email="guest@test.com", role=Role.USER)

    app.dependency_overrides[get_current_user] = override_user_1

    today = date.today()
    create_resp = await async_client.post("/api/bookings/", json={
        "check_in": str(today + timedelta(days=20)),
        "check_out": str(today + timedelta(days=22)),
        "guests": 1,
        "room_id": data["room_id"]
    })
    booking_id = create_resp.json()["booking_id"]

    # 2. Намагаємося отримати це бронювання від імені "іншого" юзера (має бути 403)
    async def override_user_2():
        return User(user_id=data["other_user_id"], email="other@test.com", role=Role.USER)

    app.dependency_overrides[get_current_user] = override_user_2

    get_resp = await async_client.get(f"/api/bookings/{booking_id}")
    assert get_resp.status_code == 403

    # 3. Намагаємося отримати те саме бронювання від імені Адміна (має бути 200)
    async def override_admin():
        return User(user_id=data["admin_id"], email="admin@test.com", role=Role.ADMIN)

    app.dependency_overrides[get_current_user] = override_admin

    admin_get_resp = await async_client.get(f"/api/bookings/{booking_id}")
    assert admin_get_resp.status_code == 200

    app.dependency_overrides.pop(get_current_user, None)
