import pytest
from httpx import AsyncClient
from src.backend.main import app
from src.backend.core.dependencies import get_admin_user
from src.backend.models.users import User, Role



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