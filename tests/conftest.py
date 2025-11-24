import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.config import settings


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def client():
    transport = ASGITransport(app=app)
    headers = {"Authorization": f"Bearer {settings.API_TOKEN}"}
    async with AsyncClient(transport=transport, base_url="http://test", headers=headers) as c:
        yield c
