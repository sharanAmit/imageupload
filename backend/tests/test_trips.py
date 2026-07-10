import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.database import Base, get_db
from backend.app.main import app
from backend.app.models import User, Trip, TripMember, Media, ActivityLog


SQLALCHEMY_DATABASE_URL = "sqlite:///./test_trips.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

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

def create_user_and_login(email: str, name: str):
    # Register
    client.post(
        "/register",
        json={"name": name, "email": email, "password": "password123"}
    )
    # Login
    resp = client.post(
        "/login",
        json={"email": email, "password": "password123"}
    )
    return resp.json()["access_token"]

def test_trip_creation_and_membership():
    token = create_user_and_login("tripowner@example.com", "Owner User")
    headers = {"Authorization": f"Bearer {token}"}

    # Create trip
    response = client.post(
        "/trip",
        headers=headers,
        json={
            "trip_name": "Trip to Japan",
            "description": "Tokyo and Kyoto visit"
        }
    )
    assert response.status_code == 201
    trip_data = response.json()
    assert trip_data["trip_name"] == "Trip to Japan"
    assert trip_data["description"] == "Tokyo and Kyoto visit"
    assert "uuid" in trip_data

    # Fetch trips list
    list_response = client.get("/trip", headers=headers)
    assert list_response.status_code == 200
    trips = list_response.json()
    assert len(trips) == 1
    assert trips[0]["uuid"] == trip_data["uuid"]

    # Fetch trip details (includes members)
    detail_response = client.get(f"/trip/{trip_data['uuid']}", headers=headers)
    assert detail_response.status_code == 200
    details = detail_response.json()
    assert len(details["members"]) == 1
    assert details["members"][0]["role"] == "owner"

def test_unauthorized_trip_access():
    owner_token = create_user_and_login("tripowner@example.com", "Owner User")
    stranger_token = create_user_and_login("stranger@example.com", "Stranger User")

    # Owner creates trip
    response = client.post(
        "/trip",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"trip_name": "Secret Trip", "description": "Owner only"}
    )
    trip_uuid = response.json()["uuid"]

    # Stranger tries to fetch trip details
    stranger_response = client.get(
        f"/trip/{trip_uuid}",
        headers={"Authorization": f"Bearer {stranger_token}"}
    )
    assert stranger_response.status_code == 403
    assert stranger_response.json()["detail"] == "Not authorized to view this trip"

def test_invite_member():
    owner_token = create_user_and_login("tripowner@example.com", "Owner User")
    invitee_token = create_user_and_login("invitee@example.com", "Invitee User")

    # Owner creates trip
    response = client.post(
        "/trip",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"trip_name": "Shared Trip", "description": "Collaborators welcome"}
    )
    trip_uuid = response.json()["uuid"]

    # Owner invites invitee
    invite_response = client.post(
        f"/trip/{trip_uuid}/invite",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={
            "email": "invitee@example.com",
            "role": "member"
        }
    )
    assert invite_response.status_code == 200
    invite_data = invite_response.json()
    assert invite_data["role"] == "member"
    assert invite_data["status"] == "pending"
    invite_token = invite_data["user"]["uuid"]

    # Invite is pending, so the invitee is NOT a member yet
    invitee_details = client.get(
        f"/trip/{trip_uuid}",
        headers={"Authorization": f"Bearer {invitee_token}"}
    )
    assert invitee_details.status_code == 403

    # Invitee accepts the invite via the public token-based endpoint
    accept_response = client.post(f"/trip/invite/{invite_token}/accept")
    assert accept_response.status_code == 200
    assert accept_response.json()["trip_name"] == "Shared Trip"

    # Now the invitee is a member and can view the trip
    invitee_details = client.get(
        f"/trip/{trip_uuid}",
        headers={"Authorization": f"Bearer {invitee_token}"}
    )
    assert invitee_details.status_code == 200
    assert len(invitee_details.json()["members"]) == 2

def test_decline_invite():
    owner_token = create_user_and_login("tripowner@example.com", "Owner User")
    invitee_token = create_user_and_login("invitee@example.com", "Invitee User")

    response = client.post(
        "/trip",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"trip_name": "Shared Trip", "description": "Collaborators welcome"}
    )
    trip_uuid = response.json()["uuid"]

    invite_response = client.post(
        f"/trip/{trip_uuid}/invite",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"email": "invitee@example.com", "role": "member"}
    )
    invite_token = invite_response.json()["user"]["uuid"]

    decline_response = client.post(f"/trip/invite/{invite_token}/decline")
    assert decline_response.status_code == 200

    # Declining does not add membership
    invitee_details = client.get(
        f"/trip/{trip_uuid}",
        headers={"Authorization": f"Bearer {invitee_token}"}
    )
    assert invitee_details.status_code == 403

    # Owner still sees the invite, now marked as declined
    owner_details = client.get(
        f"/trip/{trip_uuid}",
        headers={"Authorization": f"Bearer {owner_token}"}
    )
    declined_entries = [m for m in owner_details.json()["members"] if m["status"] == "declined"]
    assert len(declined_entries) == 1

    # Responding again should fail — the invite has already been resolved
    second_accept = client.post(f"/trip/invite/{invite_token}/accept")
    assert second_accept.status_code == 404

def test_user_search():
    # Create two users
    create_user_and_login("searchable1@example.com", "Search User One")
    token = create_user_and_login("searchable2@example.com", "Search User Two")
    
    # Search for "One"
    response = client.get(
        "/users/search?q=One",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["name"] == "Search User One"
    assert data[0]["email"] == "searchable1@example.com"

def test_guest_invite_and_autojoin():
    owner_token = create_user_and_login("tripowner@example.com", "Owner User")
    
    # Owner creates trip
    response = client.post(
        "/trip",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"trip_name": "Shared Trip", "description": "Collaborators welcome"}
    )
    trip_uuid = response.json()["uuid"]
    
    # Invite guest email (does not exist in DB)
    guest_email = "guestuser@example.com"
    invite_response = client.post(
        f"/trip/{trip_uuid}/invite",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={
            "email": guest_email,
            "role": "member"
        }
    )
    assert invite_response.status_code == 200
    invite_data = invite_response.json()
    assert invite_data["user"]["name"] == "Pending Invite"
    assert invite_data["user"]["email"] == guest_email
    
    # The guest token is returned in mock user's uuid field
    invite_token = invite_data["user"]["uuid"]
    assert invite_token is not None
    assert invite_token != "pending"
    
    # Verify invite details can be retrieved publicly
    details_resp = client.get(f"/auth/invite/{invite_token}")
    assert details_resp.status_code == 200
    details = details_resp.json()
    assert details["trip_name"] == "Shared Trip"
    assert details["email"] == guest_email
    
    # Guest registers using the invite token
    register_response = client.post(
        f"/register?invite_token={invite_token}",
        json={
            "name": "Guest User",
            "email": guest_email,
            "password": "guestpassword123"
        }
    )
    assert register_response.status_code == 201
    
    # Login as guest
    login_response = client.post(
        "/login",
        json={"email": guest_email, "password": "guestpassword123"}
    )
    assert login_response.status_code == 200
    guest_token = login_response.json()["access_token"]
    
    # Verify guest can now fetch trip details (meaning they successfully auto-joined!)
    trip_details = client.get(
        f"/trip/{trip_uuid}",
        headers={"Authorization": f"Bearer {guest_token}"}
    )
    assert trip_details.status_code == 200
    details_json = trip_details.json()
    # Check members contains guest
    member_emails = [m["user"]["email"] for m in details_json["members"]]
    assert guest_email in member_emails

def test_update_member_role():
    owner_token = create_user_and_login("tripowner@example.com", "Owner User")
    invitee_token = create_user_and_login("invitee@example.com", "Invitee User")
    
    # Owner creates trip
    response = client.post(
        "/trip",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"trip_name": "Shared Trip", "description": "Collaborators welcome"}
    )
    trip_uuid = response.json()["uuid"]
    
    # Owner invites invitee as member
    invite_resp = client.post(
        f"/trip/{trip_uuid}/invite",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={
            "email": "invitee@example.com",
            "role": "member"
        }
    )
    assert invite_resp.status_code == 200
    member_id = invite_resp.json()["id"]
    
    # Owner updates invitee role to co-owner
    update_resp = client.put(
        f"/trip/{trip_uuid}/member/{member_id}/role",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"role": "co-owner"}
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["role"] == "co-owner"

def test_delete_pending_invite():
    owner_token = create_user_and_login("tripowner@example.com", "Owner User")
    
    # Owner creates trip
    response = client.post(
        "/trip",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"trip_name": "Shared Trip", "description": "Collaborators welcome"}
    )
    trip_uuid = response.json()["uuid"]
    
    # Invite guest email (does not exist in DB)
    guest_email = "guestuser@example.com"
    invite_response = client.post(
        f"/trip/{trip_uuid}/invite",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={
            "email": guest_email,
            "role": "member"
        }
    )
    assert invite_response.status_code == 200
    invite_id = invite_response.json()["id"]
    assert invite_id < 0
    
    # Owner cancels/deletes the pending invite
    delete_resp = client.delete(
        f"/trip/{trip_uuid}/member/{invite_id}",
        headers={"Authorization": f"Bearer {owner_token}"}
    )
    assert delete_resp.status_code == 204
    
    # Check that it is removed from trip details
    trip_details = client.get(
        f"/trip/{trip_uuid}",
        headers={"Authorization": f"Bearer {owner_token}"}
    )
    assert len(trip_details.json()["members"]) == 1  # Only owner remains



