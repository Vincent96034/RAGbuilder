# conftest.py
import pytest
from unittest.mock import patch, Mock

from fastapi.testclient import TestClient

from app.ops.user_ops import get_current_user
from app.schemas import CurrentUserSchema
from app.main import app
from app.db.models import UserModel



## v1 mocks

# Sample user data
user_id = "user123"
email = "user@example.com"
first_name = "John"
last_name = "Doe"
password = "securePassword123"


##########################################################################################
# FIREBSE AUTH

@pytest.fixture
def mock_auth_verify_id_token_success():
    with patch('app.ops.user_ops.auth.verify_id_token') as mock:
        mock.return_value = {"email": email, "user_id": user_id}
        yield mock


@pytest.fixture
def mock_auth_verify_id_token_failure(exception):
    with patch('app.ops.user_ops.auth.verify_id_token') as mock:
        mock.side_effect = exception("Mocked exception")
        yield mock


@pytest.fixture
def mock_firebase_user():
    """Fixture for mocking a Firebase user creation."""
    class MockUserRecord:
        def __init__(self, uid, email, display_name, email_verified, disabled):
            self.uid = uid
            self.email = email
            self.display_name = display_name
            self.email_verified = email_verified
            self.disabled = disabled
            self.user_metadata = MockUserMetadata()

    class MockUserMetadata:
        creation_timestamp = "2023-01-01T00:00:00Z"

    return MockUserRecord(user_id, email, f"{first_name} {last_name}", False, False)


##########################################################################################
# FIRESTORE

@pytest.fixture
def mock_firestore_client(mocker):
    mock_client = mocker.patch('app.ops.project_ops.firestore.client')
    mock_doc_ref = Mock()
    mock_client.collection.return_value.document.return_value = mock_doc_ref
    return mock_client, mock_doc_ref





## v0 mocks
# @pytest.fixture(scope="session")
# def engine():
#     """Fixture that returns a SQLAlchemy engine connected to an in-memory SQLite db."""
#     return create_engine(
#         "sqlite:///:memory:",
#         connect_args={"check_same_thread": False},
#         poolclass=StaticPool,
#     )


# @pytest.fixture(scope="session")
# def TestingSessionLocal(engine):
#     """Fixture that returns a sessionmaker object for testing purposes."""
#     return sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def client():
    """Fixture that sets up a TestClient for testing purposes."""
    with TestClient(app) as client:
        yield client


# @pytest.fixture(scope="function")
# def db_dependency(TestingSessionLocal, engine):
#     Base.metadata.create_all(bind=engine)  # Create the tables in the in-memory database
#     db = TestingSessionLocal()
#     # Insert test data
#     test_users = [
#         UserModel(email="user1@example.com", hashed_password=bcrypt.hash("password1")),
#         UserModel(email="user2@example.com", hashed_password=bcrypt.hash("password2")),
#         UserModel(email="user_delete@example.com",
#                   hashed_password=bcrypt.hash("password_delete")),
#     ]
#     db.add_all(test_users)
#     db.commit()
#     # Override get_db dependency with this session

#     def override_get_db():
#         try:
#             yield db
#         finally:
#             db.close()
#     app.dependency_overrides[get_db] = override_get_db
#     yield db
#     # Clean up the database
#     db.query(UserModel).delete()
#     db.commit()
#     Base.metadata.drop_all(bind=engine)


@pytest.fixture
def current_user_dependency():
    """Override the get_current_user dependency to return a mock user.

    Mock user: CurrentUserSchema(email='mock@example.com', user_id=1)
    """
    async def mock_get_current_user():
        # Return a mock user object, adjust the attributes to match your CurrentUserSchema
        return CurrentUserSchema(email="user1@example.com", user_id=1)

    app.dependency_overrides[get_current_user] = mock_get_current_user
    yield
    # Remove the override after the test to ensure it doesn't affect other tests
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def current_user_dependency_factory():
    """A fixture to override the get_current_user dependency with a specified user."""
    def _override(user: CurrentUserSchema):
        async def mock_get_current_user():
            return user
        app.dependency_overrides[get_current_user] = mock_get_current_user
        return mock_get_current_user
    yield _override
    # Ensure cleanup is done after each test
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def mock_env_vars(monkeypatch):
    monkeypatch.setenv("ENCRYPTION_SECRET_KEY", "secret")
    monkeypatch.setenv("ENCRYPTION_ALGORITHM", "HS256")


# @pytest.fixture
# def mock_db_session():
#     """Fixture to mock the database session."""
#     session = MagicMock(spec=Session)
#     return session


@pytest.fixture
def mock_user():
    """Fixture to create a mock user."""
    user = UserModel(email="test@example.com", hashed_password="hashedpassword")
    return user
