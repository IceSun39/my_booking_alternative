import pytest
from httpx import AsyncClient
from src.backend.main import app
from tests.conftest import TestingSessionLocal
from src.backend.models import User, Role, Property
from src.backend.models.favorites import Favorite
from src.backend.core.dependencies import get_current_user


@pytest.fixture
async def setup_favorites_data():
    """Створюємо тестові дані: юзера, два готелі та один запис в обраному"""
    async with TestingSessionLocal() as session:
        # 1. Створюємо користувача
        user = User(
            email="favorite_tester@test.com",
            password="hashed",
            username="fav_tester",
            role=Role.USER
        )
        session.add(user)
        await session.flush()
        user_id = user.user_id

        # 2. Створюємо два готелі
        prop1 = Property(
            name="Hotel One",
            country="Україна",
            city="Київ",
            street="Хрещатик",
            house_number="1",
            owner_id=user_id
        )
        prop2 = Property(
            name="Hotel Two",
            country="Україна",
            city="Львів",
            street="Площа Ринок",
            house_number="2",
            owner_id=user_id
        )
        session.add_all([prop1, prop2])
        await session.flush()

        prop1_id = prop1.property_id
        prop2_id = prop2.property_id

        # 3. Додаємо перший готель в обране (для перевірки видалення і дублікатів)
        fav = Favorite(user_id=user_id, property_id=prop1_id)
        session.add(fav)
        await session.flush()

        # Зберігаємо все
        await session.commit()

        return {
            "user_id": user_id,
            "prop1_id": prop1_id,  # Вже є в обраному
            "prop2_id": prop2_id  # Ще немає в обраному
        }


@pytest.mark.asyncio
async def test_add_to_favorites_success(async_client: AsyncClient, setup_favorites_data):
    """Тестуємо успішне додавання готелю до обраного"""
    data = setup_favorites_data

    async def override_get_current_user():
        return User(user_id=data["user_id"], email="favorite_tester@test.com", role=Role.USER)

    app.dependency_overrides[get_current_user] = override_get_current_user

    # Додаємо prop2, якого ще немає в обраному
    payload = {"property_id": data["prop2_id"]}

    response = await async_client.post("/api/favorites/", json=payload)

    assert response.status_code == 201
    res_data = response.json()
    assert res_data["user_id"] == data["user_id"]
    assert res_data["property_id"] == data["prop2_id"]

    app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_add_to_favorites_conflict(async_client: AsyncClient, setup_favorites_data):
    """Тестуємо помилку 400, якщо готель вже є в обраному"""
    data = setup_favorites_data

    async def override_get_current_user():
        return User(user_id=data["user_id"], email="favorite_tester@test.com", role=Role.USER)

    app.dependency_overrides[get_current_user] = override_get_current_user

    # Спробуємо додати prop1, який вже додали у фікстурі
    payload = {"property_id": data["prop1_id"]}

    response = await async_client.post("/api/favorites/", json=payload)

    assert response.status_code == 400
    assert response.json()["detail"] == "Already in favorites"

    app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_get_my_favorites(async_client: AsyncClient, setup_favorites_data):
    """Тестуємо отримання списку обраного"""
    data = setup_favorites_data

    async def override_get_current_user():
        return User(user_id=data["user_id"], email="favorite_tester@test.com", role=Role.USER)

    app.dependency_overrides[get_current_user] = override_get_current_user

    response = await async_client.get("/api/favorites/")

    assert response.status_code == 200
    res_data = response.json()
    assert isinstance(res_data, list)
    # Мінімум 1 (той, що створили у фікстурі)
    assert len(res_data) >= 1
    # Перевіряємо, чи повернувся правильний property_id
    assert any(fav["property_id"] == data["prop1_id"] for fav in res_data)

    app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_delete_favorite_success(async_client: AsyncClient, setup_favorites_data):
    """Тестуємо успішне видалення з обраного"""
    data = setup_favorites_data

    async def override_get_current_user():
        return User(user_id=data["user_id"], email="favorite_tester@test.com", role=Role.USER)

    app.dependency_overrides[get_current_user] = override_get_current_user

    # Видаляємо prop1
    response = await async_client.delete(f"/api/favorites/{data['prop1_id']}")

    assert response.status_code == 204

    # Перевіряємо, що його більше немає
    get_response = await async_client.get("/api/favorites/")
    assert get_response.status_code == 200
    res_data = get_response.json()
    assert not any(fav["property_id"] == data["prop1_id"] for fav in res_data)

    app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_delete_favorite_not_found(async_client: AsyncClient, setup_favorites_data):
    """Тестуємо помилку 404, якщо намагаємося видалити те, чого немає"""
    data = setup_favorites_data

    async def override_get_current_user():
        return User(user_id=data["user_id"], email="favorite_tester@test.com", role=Role.USER)

    app.dependency_overrides[get_current_user] = override_get_current_user

    # Неіснуючий property_id
    fake_property_id = 999999
    response = await async_client.delete(f"/api/favorites/{fake_property_id}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Favorite not found"

    app.dependency_overrides.pop(get_current_user, None)