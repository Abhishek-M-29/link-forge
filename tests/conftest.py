import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database.session import Base, get_db
from app.database.config import DATABASE_URL

# Use the same database URL, but we will roll back transactions
engine = create_engine(DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    # We do not drop tables, we just run on the existing schema

@pytest.fixture
def db_session():
    """Returns a sqlalchemy session, and after the test tears down everything inside a transaction"""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

from app.middleware.rate_limit import limiter
@pytest.fixture(autouse=True)
def reset_rate_limit():
    # Disable rate limiting globally for tests to prevent 429 errors
    limiter.enabled = False
    yield
    limiter.enabled = True

@pytest.fixture
def client(db_session):
    """Returns a TestClient that uses the rolled-back db session"""
    def override_get_db():
        yield db_session
        
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture()
def auth_headers_for_two_users(client):
    def register_and_login(username, email):
        client.post("/api/v1/auth/register", json={"username": username, "email": email, "password": "supersecret1"})
        login = client.post("/api/v1/auth/login", json={"email": email, "password": "supersecret1"})
        token = login.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    return register_and_login("user_a", "a@example.com"), register_and_login("user_b", "b@example.com")
