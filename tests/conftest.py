"""Shared test fixtures: an isolated in-memory DB and a seeded facility/admin user."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models.facility import Facility
from app.models.user import Role, User
from app.services.security import hash_password

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _override_get_db():
    """Yield a session bound to the isolated in-memory test database."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _override_get_db


@pytest.fixture(autouse=True)
def _fresh_schema():
    """Recreate all tables before each test so tests don't leak state into each other."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    """A DB session for setting up or inspecting test data directly."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client():
    """A TestClient wired to the isolated test database."""
    return TestClient(app)


ADMIN_PASSWORD = "TestPass123!"


@pytest.fixture
def seeded_admin(db_session):
    """A facility and an active admin user, returned with the known plaintext password."""
    facility = Facility(name="Test Clinic", city="Lahore", address="1 Test Rd", license_number="LIC-1")
    db_session.add(facility)
    db_session.flush()

    admin = User(
        facility_id=facility.id,
        full_name="Admin User",
        email="admin@test-clinic.pk",
        password_hash=hash_password(ADMIN_PASSWORD),
        role=Role.ADMIN,
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    db_session.refresh(facility)
    return facility, admin, ADMIN_PASSWORD
