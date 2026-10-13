from alembic import command
from alembic.config import Config


def pytest_sessionstart(session) -> None:
    """Apply schema migrations before integration tests use the configured test database."""
    config = Config("alembic.ini")
    command.upgrade(config, "head")
