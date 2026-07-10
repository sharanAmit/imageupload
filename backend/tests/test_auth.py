import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.database import Base, get_db
from backend.app.main import app
from backend.app.services.auth_service import AuthService
from backend.app.models import User, Trip, TripMember, Media, ActivityLog


# Use an in-memory SQLite database for unit testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override the get_db dependency in the FastAPI application
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(autouse=True)
def setup_db():
    # Setup dependency override for this test module
    app.dependency_overrides[get_db] = override_get_db
    # Create tables before each test
    Base.metadata.create_all(bind=engine)
    yield
    # Drop tables after each test
    Base.metadata.drop_all(bind=engine)
    # Clean up dependency override to avoid leakage
    app.dependency_overrides.pop(get_db, None)


client = TestClient(app)

def test_user_registration():
    response = client.post(
        "/register",
        json={
            "name": "Jane Doe",
            "email": "jane.doe@example.com",
            "password": "strongpassword123"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Jane Doe"
    assert data["email"] == "jane.doe@example.com"
    assert "id" in data
    assert "uuid" in data
    assert "password_hash" not in data

def test_user_registration_duplicate_email():
    # First registration
    client.post(
        "/register",
        json={
            "name": "Jane Doe",
            "email": "jane.doe@example.com",
            "password": "strongpassword123"
        }
    )
    # Second registration with same email
    response = client.post(
        "/register",
        json={
            "name": "Jane Smith",
            "email": "jane.doe@example.com",
            "password": "anotherpassword123"
        }
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"

def test_user_login_success():
    # Register
    client.post(
        "/register",
        json={
            "name": "Jane Doe",
            "email": "jane.doe@example.com",
            "password": "strongpassword123"
        }
    )
    # Login
    response = client.post(
        "/login",
        json={
            "email": "jane.doe@example.com",
            "password": "strongpassword123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"

def test_user_login_invalid_password():
    # Register
    client.post(
        "/register",
        json={
            "name": "Jane Doe",
            "email": "jane.doe@example.com",
            "password": "strongpassword123"
        }
    )
    # Login with wrong password
    response = client.post(
        "/login",
        json={
            "email": "jane.doe@example.com",
            "password": "wrongpassword"
        }
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"

def test_get_current_user_profile():
    # Register
    client.post(
        "/register",
        json={
            "name": "Jane Doe",
            "email": "jane.doe@example.com",
            "password": "strongpassword123"
        }
    )
    # Login
    login_resp = client.post(
        "/login",
        json={
            "email": "jane.doe@example.com",
            "password": "strongpassword123"
        }
    )
    tokens = login_resp.json()
    access_token = tokens["access_token"]

    # Get profile
    profile_resp = client.get(
        "/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert profile_resp.status_code == 200
    data = profile_resp.json()
    assert data["name"] == "Jane Doe"
    assert data["email"] == "jane.doe@example.com"

def test_google_login_success(monkeypatch):
    class MockResponse:
        status_code = 200
        def json(self):
            return {
                "email": "googleuser@example.com",
                "name": "Google User",
                "picture": "https://lh3.googleusercontent.com/a/mockpic",
                "aud": "mockclientid"
            }

    # Mock settings.GOOGLE_CLIENT_ID
    from backend.app.config import settings
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_ID", "mockclientid")

    # Mock httpx.get
    import httpx
    monkeypatch.setattr(httpx, "get", lambda *args, **kwargs: MockResponse())

    response = client.post(
        "/auth/google",
        json={"id_token": "mock_google_id_token"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data

def test_google_login_with_invite(monkeypatch):
    class MockResponse:
        status_code = 200
        def json(self):
            return {
                "email": "invitedgoogleuser@example.com",
                "name": "Invited Google User",
                "picture": "https://lh3.googleusercontent.com/a/mockpic",
                "aud": "mockclientid"
            }

    # Mock settings.GOOGLE_CLIENT_ID
    from backend.app.config import settings
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_ID", "mockclientid")

    # Mock httpx.get
    import httpx
    monkeypatch.setattr(httpx, "get", lambda *args, **kwargs: MockResponse())

    # Create owner and trip first
    db = next(override_get_db())
    owner = User(
        name="Owner User",
        email="owner@example.com",
        password_hash="pwd"
    )
    db.add(owner)
    db.commit()
    db.refresh(owner)

    trip = Trip(
        trip_name="Test Invite Trip",
        description="Testing invite link with Google login",
        created_by=owner.id
    )
    db.add(trip)
    db.commit()
    db.refresh(trip)

    # Add owner as owner member
    from backend.app.models import TripMember, TripInvite
    owner_member = TripMember(trip_id=trip.id, user_id=owner.id, role="owner")
    db.add(owner_member)

    # Create invitation for Google user
    invite = TripInvite(
        trip_id=trip.id,
        email="invitedgoogleuser@example.com",
        role="member"
    )
    db.add(invite)
    db.commit()
    db.refresh(invite)
    
    invite_token = invite.uuid

    # Now login the Google user, passing the invite_token
    response = client.post(
        f"/auth/google?invite_token={invite_token}",
        json={"id_token": "mock_google_id_token"}
    )
    assert response.status_code == 200
    
    # Get the newly created user in db
    new_user = db.query(User).filter(User.email == "invitedgoogleuser@example.com").first()
    assert new_user is not None
    
    # Verify they were automatically added to the trip!
    member = db.query(TripMember).filter(
        TripMember.trip_id == trip.id,
        TripMember.user_id == new_user.id
    ).first()
    assert member is not None
    assert member.role == "member"
    
    # Verify invite is marked as accepted
    db.refresh(invite)
    assert invite.status == "accepted"


