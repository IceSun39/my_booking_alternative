import pytest
from httpx import AsyncClient
from src.backend.main import app
from tests.conftest import TestingSessionLocal
from src.backend.models import User, Role, Property
from src.backend.core.dependencies import get_owner_or_admin_user


@pytest.fixture
async def setup_properties_data():
    """Створюємо базові дані: власника, адміна та один готель"""
    async with TestingSessionLocal() as session:
        # 1. Власник
        owner = User(email="owner@prop.com", password="pwd", username="owner1", role=Role.OWNER)
        # 2. Адмін
        admin = User(email="admin@prop.com", password="pwd", username="admin1", role=Role.ADMIN)
        # 3. Звичайний юзер (не має прав)
        user = User(email="user@prop.com", password="pwd", username="user1", role=Role.USER)

        session.add_all([owner, admin, user])
        await session.flush()

        # 4. Готель, що належить власнику
        prop = Property(
            name="Grand Hotel",
            country="Україна",
            city="Київ",
            street="Хрещатик",
            house_number="1",
            description="Nice place",
            owner_id=owner.user_id,
            rating=0.0,
            reviews_count=0
        )
        session.add(prop)
        await session.flush()

        prop_id = prop.property_id

        # Зберігаємо ID та комітимо
        data = {
            "owner_id": owner.user_id,
            "admin_id": admin.user_id,
            "user_id": user.user_id,
            "property_id": prop_id
        }
        await session.commit()
        return data


@pytest.mark.asyncio
async def test_get_all_properties(async_client: AsyncClient, setup_properties_data):
    """Тест отримання списку готелів (доступно всім)"""
    response = await async_client.get("/api/properties/")
    assert response.status_code == 200
    assert len(response.json()) >= 1


@pytest.mark.asyncio
async def test_create_property_success(async_client: AsyncClient, setup_properties_data):
    """Тест створення готелю власником"""
    data = setup_properties_data

    async def override_owner():
        return User(user_id=data["owner_id"], email="owner@prop.com", role=Role.OWNER)

    app.dependency_overrides[get_owner_or_admin_user] = override_owner

    payload = {
        "name": "New Hotel",
        "country": "Україна",
        "city": "Львів",
        "street": "Ринок",
        "house_number": "10",
        "description": "Very nice",
        "owner_id": data["owner_id"]
    }

    response = await async_client.post("/api/properties/", json=payload)
    assert response.status_code == 200
    assert response.json()["name"] == "New Hotel"

    app.dependency_overrides.pop(get_owner_or_admin_user, None)


@pytest.mark.asyncio
async def test_create_property_conflict(async_client: AsyncClient, setup_properties_data):
    """Тест на унікальність імені (409 Conflict)"""
    data = setup_properties_data

    async def override_owner():
        return User(user_id=data["owner_id"], email="owner@prop.com", role=Role.OWNER)

    app.dependency_overrides[get_owner_or_admin_user] = override_owner

    # Пробуємо створити готель з іменем, яке вже є в БД (створене у фікстурі)
    payload = {
        "name": "Grand Hotel",
        "country": "Україна",
        "city": "Київ",
        "street": "Хрещатик",
        "house_number": "1",
        "description": "Nice place",
        "owner_id": data["owner_id"]
    }

    response = await async_client.post("/api/properties/", json=payload)
    assert response.status_code == 409

    app.dependency_overrides.pop(get_owner_or_admin_user, None)


@pytest.mark.asyncio
async def test_update_property_success(async_client: AsyncClient, setup_properties_data):
    """Тест оновлення даних власником"""
    data = setup_properties_data

    async def override_owner():
        return User(user_id=data["owner_id"], email="owner@prop.com", role=Role.OWNER)

    app.dependency_overrides[get_owner_or_admin_user] = override_owner

    payload = {"city": "Одеса"}

    response = await async_client.put(f"/api/properties/{data['property_id']}", json=payload)
    assert response.status_code == 200
    assert response.json()["city"] == "Одеса"

    app.dependency_overrides.pop(get_owner_or_admin_user, None)


@pytest.mark.asyncio
async def test_delete_property_forbidden(async_client: AsyncClient, setup_properties_data):
    """Тест: звичайний користувач намагається видалити готель (має бути 403 або 401 через dependency)"""
    data = setup_properties_data

    # Зверни увагу: звичайного юзера роутер має відкинути ще на етапі Depends(get_owner_or_admin_user),
    # але навіть якщо пропустить, check_owner_or_admin видасть 403
    async def override_user():
        return User(user_id=data["user_id"], email="user@prop.com", role=Role.USER)

    app.dependency_overrides[get_owner_or_admin_user] = override_user

    response = await async_client.delete(f"/api/properties/{data['property_id']}")
    assert response.status_code in [403, 401]  # В залежності від твоєї реалізації get_owner_or_admin_user

    app.dependency_overrides.pop(get_owner_or_admin_user, None)


@pytest.mark.asyncio
async def test_delete_property_by_admin(async_client: AsyncClient, setup_properties_data):
    """Тест: адмін успішно видаляє готель, хоча він не є його власником"""
    data = setup_properties_data

    async def override_admin():
        return User(user_id=data["admin_id"], email="admin@prop.com", role=Role.ADMIN)

    app.dependency_overrides[get_owner_or_admin_user] = override_admin

    response = await async_client.delete(f"/api/properties/{data['property_id']}")
    assert response.status_code == 204

    # Перевіряємо, що готель дійсно видалено
    get_response = await async_client.get(f"/api/properties/{data['property_id']}")
    assert get_response.status_code == 404

    app.dependency_overrides.pop(get_owner_or_admin_user, None)