from fastapi.testclient import TestClient
from sqlalchemy import text

from app.db import engine
from app.main import app


def test_health() -> None:
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


def test_health_checks_database_connectivity() -> None:
    import asyncio

    async def check_database() -> None:
        async with engine.connect() as connection:
            result = await connection.execute(text("SELECT 1"))
            assert result.scalar_one() == 1

    asyncio.run(check_database())
