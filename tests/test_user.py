import pytest
from httpx import AsyncClient

from src.backend.main import app
from tests.conftest import TestingSessionLocal
from src.backend.models import User, Role
from src.backend.core.security import get_password_hash
from src.backend.core.dependencies import get_current_user, get_admin_user


def override_user(user_id: int, role: Role, email: str = "x@test.com"):
    async def _override():
        return User(user_id=user_id, email=email, username="x", phone_number="+380000000000", role=role)

    return _override


@pytest.fixture
async def setup_user_data():
    async with TestingSessionLocal() as session:
        admin = User(
            email="admin_u@test.com", username="admin_u", phone_number="+380000000001",
            password=get_password_hash("adminpass"), role=Role.ADMIN,
        )
        target = User(
            email="target_u@test.com", username="target_u", phone_number="+380000000002",
            password=get_password_hash("targetpass"), role=Role.USER,
        )
        session.add_all([admin, target])
        await session.flush()
        admin_id = admin.user_id
        target_id = target.user_id
        target_password_hash = target.password

        await session.commit()

        return {
            "admin_id": admin_id,
            "target_id": target_id,
            "target_password_hash": target_password_hash,
        }


@pytest.mark.asyncio
async def test_get_me(async_client: AsyncClient, setup_user_data):
    data = setup_user_data
    app.dependency_overrides[get_current_user] = override_user(data["target_id"], Role.USER, email="target_u@test.com")
    try:
        response = await async_client.get("/api/user/me")
        assert response.status_code == 200, response.json()
        assert response.json()["email"] == "target_u@test.com"
        assert "password" not in response.json()
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_get_user_by_id_as_admin(async_client: AsyncClient, setup_user_data):
    data = setup_user_data
    app.dependency_overrides[get_current_user] = override_user(data["admin_id"], Role.ADMIN)
    try:
        response = await async_client.get(f"/api/user/{data['target_id']}")
        assert response.status_code == 200, response.json()
        assert response.json()["user_id"] == data["target_id"]
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_get_user_not_found(async_client: AsyncClient, setup_user_data):
    data = setup_user_data
    app.dependency_overrides[get_current_user] = override_user(data["admin_id"], Role.ADMIN)
    try:
        response = await async_client.get("/api/user/999999")
        assert response.status_code == 404
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_get_user_success_for_self(async_client: AsyncClient, setup_user_data):
    """Юзер може переглядати власний профіль"""
    data = setup_user_data
    app.dependency_overrides[get_current_user] = override_user(data["target_id"], Role.USER)

    response = await async_client.get(f"/api/user/{data['target_id']}")
    assert response.status_code == 200
    assert response.json()["user_id"] == data["target_id"]


@pytest.mark.asyncio
async def test_get_user_forbidden_for_other_user(async_client: AsyncClient, setup_user_data):
    """Юзер НЕ може переглядати чужий профіль"""
    data = setup_user_data
    # Авторизуємось під неіснуючим лівим юзером (ID=999)
    app.dependency_overrides[get_current_user] = override_user(999, Role.USER)

    response = await async_client.get(f"/api/user/{data['target_id']}")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_user_success_as_admin(async_client: AsyncClient, setup_user_data):
    data = setup_user_data
    app.dependency_overrides[get_current_user] = override_user(data["admin_id"], Role.ADMIN)
    try:
        payload = {
            "email": "new_u@test.com",
            "username": "new_u",
            "phone_number": "+380000000099",
            "password": "somepassword",
        }
        response = await async_client.post("/api/user/", json=payload)
        assert response.status_code == 201, response.json()
        body = response.json()
        assert body["email"] == "new_u@test.com"
        assert "password" not in body
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_create_user_duplicate_email_fails(async_client: AsyncClient, setup_user_data):
    data = setup_user_data
    app.dependency_overrides[get_current_user] = override_user(data["admin_id"], Role.ADMIN)
    try:
        payload = {
            "email": "target_u@test.com",  # вже існує
            "username": "someone_else",
            "phone_number": "+380000000098",
            "password": "somepassword",
        }
        response = await async_client.post("/api/user/", json=payload)
        assert response.status_code == 400
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_update_user_success_as_admin(async_client: AsyncClient, setup_user_data):
    data = setup_user_data
    app.dependency_overrides[get_current_user] = override_user(data["admin_id"], Role.ADMIN)
    try:
        payload = {"username": "renamed_target"}
        response = await async_client.put(f"/api/user/{data['target_id']}", json=payload)
        assert response.status_code == 200, response.json()
        assert response.json()["username"] == "renamed_target"
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_update_user_password_is_hashed(async_client: AsyncClient, setup_user_data):
    data = setup_user_data
    app.dependency_overrides[get_current_user] = override_user(data["admin_id"], Role.ADMIN)
    try:
        payload = {"password": "brandNewPassword123"}
        response = await async_client.put(f"/api/user/{data['target_id']}", json=payload)
        assert response.status_code == 200, response.json()
        assert "password" not in response.json()
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    async with TestingSessionLocal() as session:
        from sqlalchemy import select
        stmt = select(User).where(User.user_id == data["target_id"])
        result = await session.execute(stmt)
        refreshed = result.scalar_one()
        assert refreshed.password != data["target_password_hash"]
        assert refreshed.password != "brandNewPassword123"  # не зберігається у відкритому вигляді


@pytest.mark.asyncio
async def test_update_user_not_found(async_client: AsyncClient, setup_user_data):
    app.dependency_overrides[get_current_user] = override_user(setup_user_data["admin_id"], Role.ADMIN)
    try:
        response = await async_client.put("/api/user/999999", json={"username": "ghost"})
        assert response.status_code == 404
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_update_user_success_for_self(async_client: AsyncClient, setup_user_data):
    """Юзер може оновлювати власні дані"""
    data = setup_user_data
    app.dependency_overrides[get_current_user] = override_user(data["target_id"], Role.USER)

    response = await async_client.put(f"/api/user/{data['target_id']}", json={"username": "self_rename"})
    assert response.status_code == 200
    assert response.json()["username"] == "self_rename"


@pytest.mark.asyncio
async def test_update_user_forbidden_for_other_user(async_client: AsyncClient, setup_user_data):
    """Юзер НЕ може оновлювати чужі дані"""
    data = setup_user_data
    # Авторизуємось під лівим юзером (ID=999)
    app.dependency_overrides[get_current_user] = override_user(999, Role.USER)

    response = await async_client.put(f"/api/user/{data['target_id']}", json={"username": "hacker_rename"})
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_user_success_as_admin(async_client: AsyncClient, setup_user_data):
    data = setup_user_data
    app.dependency_overrides[get_current_user] = override_user(data["admin_id"], Role.ADMIN)
    try:
        response = await async_client.delete(f"/api/user/{data['target_id']}")
        assert response.status_code == 204

        follow_up = await async_client.get(f"/api/user/{data['target_id']}")
        assert follow_up.status_code == 404
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_delete_user_not_found(async_client: AsyncClient, setup_user_data):
    app.dependency_overrides[get_current_user] = override_user(setup_user_data["admin_id"], Role.ADMIN)
    try:
        response = await async_client.delete("/api/user/999999")
        assert response.status_code == 404
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_delete_user_forbidden_for_other_user(async_client: AsyncClient, setup_user_data):
    """Юзер НЕ може видаляти чужий профіль"""
    data = setup_user_data
    # Авторизуємось під лівим юзером (ID=999)
    app.dependency_overrides[get_current_user] = override_user(999, Role.USER)

    response = await async_client.delete(f"/api/user/{data['target_id']}")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_user_success_for_self(async_client: AsyncClient, setup_user_data):
    """Юзер може видалити власний профіль (Цей тест має йти останнім, щоб не зламати інші)"""
    data = setup_user_data
    app.dependency_overrides[get_current_user] = override_user(data["target_id"], Role.USER)

    response = await async_client.delete(f"/api/user/{data['target_id']}")
    assert response.status_code == 204
