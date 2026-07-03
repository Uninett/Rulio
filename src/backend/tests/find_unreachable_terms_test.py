import pytest

from backend.objects.attributes.address import Address
from backend.objects.attributes.service import Service
from backend.services.find_unreachable_terms import find_potentially_unreachable_terms
from backend.services.generate_config import Policy, PolicyRule


@pytest.mark.django_db
def test_find_potentially_unreachable_terms_detects_shadowed_terms(request_with_session, create_testing_tenant):
    vendor_policy_type_pairs = [
        ("juniper", ""),
        ("arista", ""),
        ("aruba", ""),
        ("cisco", "mixed"),
        ("brocade", ""),
        ("paloalto", ["from-zone", "internal", "to-zone", "external", "mixed"]),
    ]

    source_supernet = Address(
        name="Unreachable_Test_Source_Supernet",
        description="Broad source network for unreachable-term test",
        tenant_id=create_testing_tenant.id,
        addr_type="network",
        ipv4_type="standard",
        ipv4Network="10.0.0.0/8",
    )
    source_supernet.save()

    source_subnet = Address(
        name="Unreachable_Test_Source_Subnet",
        description="Narrow source network for unreachable-term test",
        tenant_id=create_testing_tenant.id,
        addr_type="network",
        ipv4_type="standard",
        ipv4Network="10.10.10.0/24",
    )
    source_subnet.save()

    destination_any = Address(
        name="Unreachable_Test_Destination_Any",
        description="Any destination for unreachable-term test",
        tenant_id=create_testing_tenant.id,
        addr_type="network",
        ipv4_type="standard",
        ipv4Network="0.0.0.0/0",
    )
    destination_any.save()

    destination_host = Address(
        name="Unreachable_Test_Destination_Host",
        description="Specific destination host for unreachable-term test",
        tenant_id=create_testing_tenant.id,
        addr_type="network",
        ipv4_type="standard",
        ipv4Network="172.16.1.10/32",
    )
    destination_host.save()

    https_broad_service = Service(
        name="Unreachable_Test_HTTPS_Broad",
        description="Broad HTTPS service for unreachable-term test",
        tenant_id=create_testing_tenant.id,
        protocol="tcp",
        port_start=443,
        port_end=443,
    )
    https_broad_service.save()

    https_same_service = Service(
        name="Unreachable_Test_HTTPS_Same",
        description="Same HTTPS service for unreachable-term test",
        tenant_id=create_testing_tenant.id,
        protocol="tcp",
        port_start=443,
        port_end=443,
    )
    https_same_service.save()

    http_service = Service(
        name="Unreachable_Test_HTTP",
        description="HTTP service for reachable-term test",
        tenant_id=create_testing_tenant.id,
        protocol="tcp",
        port_start=80,
        port_end=80,
    )
    http_service.save()

    policy_rules = [
        PolicyRule(
            name="Broad_HTTPS_Source",
            obj_type="address",
            action="accept",
            object=source_supernet,
            direction="source",
            sequence=10,
        ),
        PolicyRule(
            name="Broad_HTTPS_Destination",
            obj_type="address",
            action="accept",
            object=destination_any,
            direction="destination",
            sequence=10,
        ),
        PolicyRule(
            name="Broad_HTTPS_Service",
            obj_type="service",
            action="accept",
            object=https_broad_service,
            direction="destination",
            sequence=10,
        ),
        PolicyRule(
            name="Shadowed_HTTPS_Source",
            obj_type="address",
            action="deny",
            object=source_subnet,
            direction="source",
            sequence=20,
        ),
        PolicyRule(
            name="Shadowed_HTTPS_Destination",
            obj_type="address",
            action="deny",
            object=destination_host,
            direction="destination",
            sequence=20,
        ),
        PolicyRule(
            name="Shadowed_HTTPS_Service",
            obj_type="service",
            action="deny",
            object=https_same_service,
            direction="destination",
            sequence=20,
        ),
        PolicyRule(
            name="Reachable_HTTP_Source",
            obj_type="address",
            action="deny",
            object=source_subnet,
            direction="source",
            sequence=30,
        ),
        PolicyRule(
            name="Reachable_HTTP_Destination",
            obj_type="address",
            action="deny",
            object=destination_host,
            direction="destination",
            sequence=30,
        ),
        PolicyRule(
            name="Reachable_HTTP_Service",
            obj_type="service",
            action="deny",
            object=http_service,
            direction="destination",
            sequence=30,
        ),
    ]

    for vendor, policy_type in vendor_policy_type_pairs:
        policy = Policy(
            name=f"Unreachable_Terms_Test_{vendor}",
            rules=policy_rules,
            vendor=vendor,
            request=request_with_session,
            policy_type=policy_type,
        )

        unreachable_terms = find_potentially_unreachable_terms(policy)

        assert isinstance(unreachable_terms, list)
        assert len(unreachable_terms) == 1

        unreachable_term = unreachable_terms[0]

        # Verify the narrower HTTPS term is flagged as shadowed by the earlier broader HTTPS term
        assert unreachable_term["term_name"].startswith("seq20-")
        assert unreachable_term["shadowed_by"].startswith("seq10-")
        assert unreachable_term["term_index"] == 1
        assert unreachable_term["shadowed_by_index"] == 0

        # Verify the analyzer reports that first-match evaluation prevents the later term from matching
        assert unreachable_term["current_action"] == "deny"
        assert unreachable_term["shadowing_action"] == "accept"
        assert "different action but earlier first-match term still prevents later match" in unreachable_term["reason"]

        # Verify the shadowing reason includes the fields that are fully covered
        assert "protocol fully covered" in unreachable_term["reason"]
        assert "source-address fully covered" in unreachable_term["reason"]
        assert "destination-address fully covered" in unreachable_term["reason"]
        assert "destination-port fully covered" in unreachable_term["reason"]

        # Verify the shadowed term had both address and port constraints
        assert unreachable_term["has_address_constraints"] is True
        assert unreachable_term["has_port_constraints"] is True

        # Verify the HTTP term is not falsely reported as unreachable
        assert not any(term["term_name"].startswith("seq30-") for term in unreachable_terms)
