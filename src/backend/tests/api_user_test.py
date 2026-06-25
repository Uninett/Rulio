from constants import GLOBAL_TENANT_ID
import pytest
from django.contrib.contenttypes.models import ContentType
from django.test import Client

from backend.objects.management.tenant import Tenant
from backend.objects.filters.rule import Rule
from backend.objects.filters.rule_match import RuleMatch
from backend.objects.attributes.address import Address
from django.contrib.auth import get_user_model
from django.test import Client
from backend.services.seed.populate import populate_db


@pytest.fixture
def authenticated_client_with_tenant():
    User = get_user_model()
    user = User.objects.create_superuser(username="admin", password="change-me")

    client = Client()
    client.force_login(user)

    session = client.session
    session["current_tenant_id"] = GLOBAL_TENANT_ID
    session.save()

    return client


@pytest.mark.django_db
def test_login():
    User = get_user_model()
    User.objects.create_user(username="admin", password="change-me")

    client = Client()
    response = client.post(
        "/api/login",
        {"username": "admin", "password": "change-me"},
        content_type="application/json",
    )

    assert response.status_code == 200
    assert "sessionid" in response.cookies


@pytest.mark.django_db
def test_who_am_i(authenticated_client_with_tenant):
    client = authenticated_client_with_tenant
    response = client.get("/api/who_am_i")

    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "admin"
    assert "current_tenant_id" in data


@pytest.mark.django_db
def test_logout(authenticated_client_with_tenant):
    client = authenticated_client_with_tenant

    response = client.post("/api/logout")
    assert response.status_code == 200

    who_am_i_response = client.get("/api/who_am_i")
    assert who_am_i_response.status_code == 200
    assert not who_am_i_response.json()["authenticated"]


@pytest.mark.django_db
def test_members(authenticated_client_with_tenant):
    client = authenticated_client_with_tenant

    response = client.get("/api/members")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    for member in data:
        assert "username" in member
        assert "email" in member


@pytest.mark.django_db
def test_create_user(authenticated_client_with_tenant):
    client = authenticated_client_with_tenant

    response = client.post(
        "/api/create_user",
        {
            "username": "newuser",
            "password": "newpassword",
            "email": "email@example.com",
        },
        content_type="application/json",
    )
    assert response.status_code == 200
    check = client.get("/api/members")
    assert check.status_code == 200
    data = check.json()
    assert any(member["username"] == "newuser" for member in data)


@pytest.mark.django_db
def test_delete_user(authenticated_client_with_tenant):
    client = authenticated_client_with_tenant

    # Create a new user to delete
    response = client.post(
        "/api/create_user",
        {
            "username": "tobedeleted",
            "password": "deletepassword",
            "email": "example@gmail.com",
        },
        content_type="application/json",
    )
    assert response.status_code == 200

    # Delete the user

    user_id = get_user_model().objects.get(username="tobedeleted").id

    response = client.delete(f"/api/delete_user?user_id={user_id}")
    assert response.status_code == 200

    # Verify the user is deleted
    check = client.get("/api/members")
    assert check.status_code == 200
    data = check.json()
    assert not any(member["username"] == "tobedeleted" for member in data)

@pytest.mark.django_db
def test_set_current_tenant(authenticated_client_with_tenant):
    client = authenticated_client_with_tenant

    response = client.post(
        "/api/create_tenant",
        {"name": "New Tenant"},
        content_type="application/json",
    )
    assert response.status_code == 200

    new_tenant = Tenant.objects.get(tenant_name="New Tenant")

    response = client.get(f"/api/set_tenant?tenant_id={new_tenant.id}")
    assert response.status_code == 200

    who_am_i_response = client.get("/api/who_am_i")
    assert who_am_i_response.status_code == 200

    data = who_am_i_response.json()
    assert data["current_tenant_id"] == str(new_tenant.id)