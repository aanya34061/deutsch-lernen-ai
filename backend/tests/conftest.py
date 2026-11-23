import pytest
import uuid
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database import connect_to_mongo, close_mongo_connection, db_instance
from app.config import settings
from app.security import _current_user_id

@pytest.fixture(autouse=True)
async def setup_db():
    original_name = settings.MONGODB_DB_NAME
    settings.MONGODB_DB_NAME = f"german_learning_test_{uuid.uuid4().hex}"
    test_name = settings.MONGODB_DB_NAME
    user_token = _current_user_id.set("default")
    try:
        await connect_to_mongo()
        yield
    finally:
        if db_instance.client is not None:
            await db_instance.client.drop_database(test_name)
        await close_mongo_connection()
        settings.MONGODB_DB_NAME = original_name
        _current_user_id.reset(user_token)

@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        credentials = {
            "username": f"learner-{uuid.uuid4().hex[:12]}",
            "password": "Test-Passphrase-4921!",
            "name": "Test Learner",
        }
        registered = await ac.post("/api/v1/auth/register", json=credentials)
        assert registered.status_code == 201
        ac.headers["X-CSRF-Token"] = registered.json()["csrf_token"]
        ac.user_id = registered.json()["id"]
        ac.username = credentials["username"]
        ac.password = credentials["password"]
        yield ac
