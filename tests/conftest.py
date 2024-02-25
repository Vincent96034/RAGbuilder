# conftest.py
import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import sessionmaker, Session
from unittest.mock import MagicMock

from app.main import app
from app.db import Base, get_db
from app.db.models import UserModel
from app.ops.user_ops import get_current_user
from app.schemas import CurrentUserSchema



@pytest.fixture(scope="session")
def engine():
    """Fixture that returns a SQLAlchemy engine connected to an in-memory SQLite db."""
    return create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


@pytest.fixture(scope="session")
def TestingSessionLocal(engine):
    """Fixture that returns a sessionmaker object for testing purposes."""
    Base.metadata.create_all(bind=engine)  # Create the tables in the in-memory database
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def client():
    """Fixture that sets up a TestClient for testing purposes."""
    with TestClient(app) as client:
        yield client


@pytest.fixture
def override_get_db(TestingSessionLocal):
    """Fixture that overrides the `get_db` dependency for testing purposes.
    This fixture creates a new database session using `TestingSessionLocal`,
    a fixture that returns a sessionmaker for an in-memory SQLite database.
    It yields the session for use in the test, and then closes the session
    after the test is finished. The `get_db` dependency in the application
    is replaced with this overridden function during the test, and then
    restored to its original state afterwards.
    """
    def _override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()
    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def override_get_current_user():
    """Override the get_current_user dependency to return a mock user.
    
    Mock user: CurrentUserSchema(email='mock@example.com', user_id=1)
    """
    async def mock_get_current_user():
        # Return a mock user object, adjust the attributes to match your CurrentUserSchema
        return CurrentUserSchema(email="mock@example.com", user_id=1)

    app.dependency_overrides[get_current_user] = mock_get_current_user
    yield
    # Remove the override after the test to ensure it doesn't affect other tests
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def mock_env_vars(monkeypatch):
    monkeypatch.setenv("ENCRYPTION_SECRET_KEY", "secret")
    monkeypatch.setenv("ENCRYPTION_ALGORITHM", "HS256")


@pytest.fixture
def mock_db_session():
    """Fixture to mock the database session."""
    session = MagicMock(spec=Session)
    return session

@pytest.fixture
def mock_user():
    """Fixture to create a mock user."""
    user = UserModel(email="test@example.com", hashed_password="hashedpassword")
    return user



