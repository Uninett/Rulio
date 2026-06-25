import pytest
from django.contrib.contenttypes.models import ContentType
from django.test import Client

from backend.objects.management.tenant import Tenant
from backend.objects.filters.rule import Rule
from backend.objects.filters.rule_match import RuleMatch
from backend.objects.attributes.address import Address
from django.contrib.auth import get_user_model
from django.test import Client


@pytest.fixture
def authenticated_client_with_tenant():
    User = get_user_model()
    user = User.objects.create_user(username="admin", password="change-me")
    tenant = Tenant.objects.create(tenant_name="Tenant A")

    client = Client()
    client.force_login(user)

    session = client.session
    session["current_tenant_id"] = tenant.id
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
