import pytest
from httpx import AsyncClient

from src.backend.main import app
from tests.conftest import TestingSessionLocal
from src.backend.models import User, Role, Property, Room
from src.backend.core.dependencies import get_current_user


def override_user(user_id: int, role: Role):
    async def _override():
        return User(user_id=user_id, email="x@test.com", role=role)
    return _override


@pytest.fixture
async def setup_room_data():
    async with TestingSessionLocal() as session:
        owner = User(email="owner_room@test.com", password="pwd", username="owner", role=Role.OWNER)
        other_owner = User(email="other_room@test.com", password="pwd", username="other_owner", role=Role.OWNER)
        admin = User(email="admin_room@test.com", password="pwd", username="admin", role=Role.ADMIN)
        session.add_all([owner, other_owner, admin])
        await session.flush()

        owner_id = owner.user_id
        other_owner_id = other_owner.user_id
        admin_id = admin.user_id

        prop = Property(
            name="Room Hotel",
            country="UA",
            city="Kyiv",
            street="B",
            house_number="2",
            description="Nice place",
            owner_id=owner_id,
            rating=0.0,
            reviews_count=0
        )
        session.add(prop)
        await session.flush()
        prop_id = prop.property_id

        room = Room(
            property_id=prop_id,
            name="Standard",
            capacity=2,
            price=80,
            is_contains_several_groups=False
        )
        session.add(room)
        await session.flush()
        room_id = room.room_id

        await session.commit()

        return {
            "owner_id": owner_id,
            "other_owner_id": other_owner_id,
            "admin_id": admin_id,
            "property_id": prop_id,
            "room_id": room_id,
        }


@pytest.mark.asyncio
async def test_get_room_success(async_client: AsyncClient, setup_room_data):
    data = setup_room_data
    app.dependency_overrides[get_current_user] = override_user(data["owner_id"], Role.USER)
    try:
        response = await async_client.get(f"/api/rooms/{data['room_id']}")
        assert response.status_code == 200, response.json()
        assert response.json()["room_id"] == data["room_id"]
        assert response.json()["name"] == "Standard"
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_get_room_not_found(async_client: AsyncClient, setup_room_data):
    data = setup_room_data
    app.dependency_overrides[get_current_user] = override_user(data["owner_id"], Role.USER)
    try:
        response = await async_client.get("/api/rooms/999999")
        assert response.status_code == 404
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_create_room_success(async_client: AsyncClient, setup_room_data):
    data = setup_room_data
    app.dependency_overrides[get_current_user] = override_user(data["owner_id"], Role.OWNER)
    try:
        payload = {
            "name": "Deluxe",
            "price": 150,
            "capacity": 3,
            "property_id": data["property_id"],
            "amenities": [],
            "is_contains_several_groups": False,
        }
        response = await async_client.post("/api/rooms/", json=payload)
        assert response.status_code == 201, response.json()
        assert response.json()["name"] == "Deluxe"
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_create_room_duplicate_fails(async_client: AsyncClient, setup_room_data):
    data = setup_room_data
    app.dependency_overrides[get_current_user] = override_user(data["owner_id"], Role.OWNER)
    try:
        payload = {
            "name": "Standard",
            "price": 100,
            "capacity": 2,
            "property_id": data["property_id"],
            "amenities": []
        }
        response = await async_client.post("/api/rooms/", json=payload)
        assert response.status_code == 400
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_create_room_forbidden_for_non_owner(async_client: AsyncClient, setup_room_data):
    data = setup_room_data
    app.dependency_overrides[get_current_user] = override_user(data["other_owner_id"], Role.OWNER)
    try:
        payload = {
            "name": "Suite",
            "price": 200,
            "capacity": 4,
            "property_id": data["property_id"],
            "amenities": []
        }
        response = await async_client.post("/api/rooms/", json=payload)
        assert response.status_code == 403
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_update_room_success(async_client: AsyncClient, setup_room_data):
    data = setup_room_data
    app.dependency_overrides[get_current_user] = override_user(data["owner_id"], Role.OWNER)
    try:
        payload = {"room_id": data["room_id"], "price": 120}
        response = await async_client.put(f"/api/rooms/{data['room_id']}", json=payload)
        assert response.status_code == 200, response.json()
        assert response.json()["price"] == 120
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_update_room_forbidden_for_non_owner(async_client: AsyncClient, setup_room_data):
    data = setup_room_data
    app.dependency_overrides[get_current_user] = override_user(data["other_owner_id"], Role.OWNER)
    try:
        payload = {"room_id": data["room_id"], "price": 999}
        response = await async_client.put(f"/api/rooms/{data['room_id']}", json=payload)
        assert response.status_code == 403
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_update_room_forbidden_for_regular_user(async_client: AsyncClient, setup_room_data):
    data = setup_room_data
    app.dependency_overrides[get_current_user] = override_user(data["owner_id"], Role.USER)
    try:
        payload = {"room_id": data["room_id"], "price": 999}
        response = await async_client.put(f"/api/rooms/{data['room_id']}", json=payload)
        assert response.status_code == 403
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_delete_room_success(async_client: AsyncClient, setup_room_data):
    data = setup_room_data
    app.dependency_overrides[get_current_user] = override_user(data["owner_id"], Role.OWNER)
    try:
        response = await async_client.delete(f"/api/rooms/{data['room_id']}")
        assert response.status_code in [200, 204], response.text
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_delete_room_forbidden_for_non_owner(async_client: AsyncClient, setup_room_data):
    data = setup_room_data
    app.dependency_overrides[get_current_user] = override_user(data["other_owner_id"], Role.OWNER)
    try:
        response = await async_client.delete(f"/api/rooms/{data['room_id']}")
        assert response.status_code == 403
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_admin_can_manage_any_room(async_client: AsyncClient, setup_room_data):
    data = setup_room_data
    app.dependency_overrides[get_current_user] = override_user(data["admin_id"], Role.ADMIN)
    try:
        payload = {"room_id": data["room_id"], "price": 300}
        response = await async_client.put(f"/api/rooms/{data['room_id']}", json=payload)
        assert response.status_code == 200, response.json()
    finally:
        app.dependency_overrides.pop(get_current_user, None)