import pytest
from django.contrib.contenttypes.models import ContentType
from django.test import Client

from backend.objects.management.tenant import Tenant
from backend.objects.filters.rule import Rule
from backend.objects.filters.rule_match import RuleMatch
from backend.objects.attributes.address import Address


@pytest.mark.django_db
def test_login():
    client = Client()
    response = client.post(
        "/api/login",
        {"username": "admin", "password": "change-me"},
        content_type="application/json",
    )
    assert response.status_code == 200
    assert "sessionid" in response.cookies


@pytest.mark.django_db
def test_list_rules_with_objects(client: Client):
    tenant = Tenant.objects.create(name="Tenant A")

    session = client.session
    session["current_tenant_id"] = tenant.id
    session.save()

    rule = Rule.objects.create(
        name="Allow DNS",
        description="Test rule",
        tenant=tenant,
        action="allow",
        log_type="start",
        created_by=1,
        changed_by=1,
        enable=True,
    )

    address = Address.objects.create(name="Server 1")
    ct = ContentType.objects.get_for_model(Address)

    RuleMatch.objects.create(
        rule=rule,
        match="source",
        content_type=ct,
        object_id=address.id,
    )

    response = client.get("/api/rules-with-objects")

    assert response.status_code == 200

    data = response.json()
    assert len(data) == 1

    rule_data = data[0]
    assert rule_data["rule_id"] == rule.id
    assert rule_data["rule_name"] == "Allow DNS"
    assert rule_data["objects"] == [
        {
            "object_type": "Address",
            "object_id": address.id,
            "object_name": "Server 1",
        }
    ]
