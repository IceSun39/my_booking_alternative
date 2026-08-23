import pytest
from httpx import AsyncClient
from src.backend.main import app
from src.backend.core.dependencies import get_admin_user
from src.backend.models.users import User, Role
from tests.conftest import TestingSessionLocal
from src.backend.models import Property, Room
from src.backend.core.dependencies import get_owner_or_admin_user


async def override_get_admin_user():
    return User(user_id=1, email="admin@test.com", role=Role.ADMIN)


app.dependency_overrides[get_admin_user] = override_get_admin_user


@pytest.mark.asyncio
async def test_create_amenity(async_client: AsyncClient):
    """Тестуємо створення зручності адміном"""
    payload = {
        "name": "Wi-Fi",
        "description": "Безкоштовний швидкісний інтернет",
        "type": "both"
    }
    response = await async_client.post("/api/amenity/", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Wi-Fi"
    assert data["description"] == "Безкоштовний швидкісний інтернет"
    assert "amenity_id" in data


@pytest.mark.asyncio
async def test_get_all_amenities(async_client: AsyncClient):
    """Тестуємо отримання списку зручностей"""
    # Спочатку створимо дві різні зручності
    await async_client.post("/api/amenity/", json={"name": "Басейн", "type": "property"})
    await async_client.post("/api/amenity/", json={"name": "Сейф", "type": "room"})

    # Перевіряємо отримання всіх
    response = await async_client.get("/api/amenity/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2

    # Перевіряємо фільтрацію через query параметр amenity_type
    response_filtered = await async_client.get("/api/amenity/?amenity_type=room")
    assert response_filtered.status_code == 200
    filtered_data = response_filtered.json()

    # Має повернути лише 'room' та 'both' (якщо ми створювали both раніше)
    assert any(item["name"] == "Сейф" for item in filtered_data)
    assert not any(item["name"] == "Басейн" for item in filtered_data)


@pytest.mark.asyncio
async def test_update_amenity(async_client: AsyncClient):
    """Тестуємо оновлення зручності"""
    # Створюємо
    create_resp = await async_client.post(
        "/api/amenity/",
        json={"name": "Старе ім'я"}
    )
    amenity_id = create_resp.json()["amenity_id"]

    # Оновлюємо
    update_payload = {"name": "Нове ім'я", "type": "property"}
    response = await async_client.put(f"/api/amenity/{amenity_id}", json=update_payload)

    assert response.status_code == 202
    data = response.json()
    assert data["name"] == "Нове ім'я"


@pytest.mark.asyncio
async def test_delete_amenity(async_client: AsyncClient):
    """Тестуємо видалення зручності"""
    # Створюємо
    create_resp = await async_client.post(
        "/api/amenity/",
        json={"name": "Для видалення"}
    )
    amenity_id = create_resp.json()["amenity_id"]

    # Видаляємо
    del_response = await async_client.delete(f"/api/amenity/{amenity_id}")
    assert del_response.status_code == 204

    # Перевіряємо, що її більше немає (очікуємо 404 при спробі оновити)
    update_resp = await async_client.put(
        f"/api/amenity/{amenity_id}",
        json={"name": "Тест"}
    )
    assert update_resp.status_code == 404


@pytest.mark.asyncio
async def test_update_property_amenities(async_client: AsyncClient):
    """Тестуємо додавання зручностей до готелю"""

    # 1. Створюємо кілька зручностей через API (від імені адміна, як у попередніх тестах)
    resp1 = await async_client.post("/api/amenity/", json={"name": "Паркінг", "type": "property"})
    resp2 = await async_client.post("/api/amenity/", json={"name": "Wi-Fi", "type": "both"})

    amenity_id_1 = resp1.json()["amenity_id"]
    amenity_id_2 = resp2.json()["amenity_id"]

    # 2. Створюємо готель напряму в тестовій базі даних
    async with TestingSessionLocal() as session:
        new_property = Property(
            name="Test Hotel",
            country="Україна",
            city="Київ",
            street="Тестова",
            house_number="1",
            owner_id=1
        )
        session.add(new_property)
        await session.commit()
        await session.refresh(new_property)
        property_id = new_property.property_id

    # 3. Перевизначаємо залежність авторизації, щоб API думало, що ми — власник (ID 1)
    async def override_get_owner():
        return User(user_id=1, email="owner@test.com", role=Role.USER)

    app.dependency_overrides[get_owner_or_admin_user] = override_get_owner

    # 4. Відправляємо запит на оновлення списку зручностей
    payload = {"amenity_ids": [amenity_id_1, amenity_id_2]}
    response = await async_client.put(f"/api/property/{property_id}/amenities/", json=payload)

    # 5. Перевіряємо результати
    assert response.status_code == 202
    data = response.json()
    assert len(data) == 2
    assert any(a["name"] == "Паркінг" for a in data)

    app.dependency_overrides.pop(get_owner_or_admin_user, None)


@pytest.mark.asyncio
async def test_update_room_amenities(async_client: AsyncClient):
    """Тестуємо додавання зручностей до кімнати"""

    # 1. Створюємо зручність типу "room"
    resp = await async_client.post("/api/amenity/", json={"name": "Кондиціонер", "type": "room"})
    amenity_id = resp.json()["amenity_id"]

    # 2. Створюємо готель, а потім кімнату в ньому
    async with TestingSessionLocal() as session:
        new_property = Property(
            name="Test Hotel",
            country="Україна",
            city="Київ",
            street="Тестова",
            house_number="1",
            owner_id=1
        )
        session.add(new_property)
        await session.commit()
        await session.refresh(new_property)

        # Обов'язкові поля для Room
        new_room = Room(
            property_id=new_property.property_id,
            name="Люкс",
            capacity=2,
            price=1500,
            is_contains_several_groups=False,
        )
        session.add(new_room)
        await session.commit()
        await session.refresh(new_room)
        room_id = new_room.room_id

    # 3. Знову стаємо власником
    async def override_get_owner():
        return User(user_id=1, email="owner@test.com", role=Role.USER)

    app.dependency_overrides[get_owner_or_admin_user] = override_get_owner

    # 4. Робимо запит
    payload = {"amenity_ids": [amenity_id]}
    response = await async_client.put(f"/api/rooms/{room_id}/amenities/", json=payload)

    # 5. Перевіряємо
    assert response.status_code == 202
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Кондиціонер"

    app.dependency_overrides.pop(get_owner_or_admin_user, None)
