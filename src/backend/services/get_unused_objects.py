from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.db.models import Exists, OuterRef, QuerySet

from backend.objects.attributes.address import Address
from backend.objects.attributes.address_group import AddressGroup
from backend.objects.attributes.address_group_member import AddressGroupMember
from backend.objects.attributes.service import Service
from backend.objects.attributes.service_group import ServiceGroup
from backend.objects.attributes.service_group_member import ServiceGroupMember
from backend.objects.attributes.tag import Tag
from backend.objects.attributes.tag_connection import TagConnection
from backend.objects.filters.filter import Filter
from backend.objects.filters.rule_match import RuleMatch
from backend.objects.tenant_objects.filter_interface import FilterInterface
from backend.services.helper_user_tenant import require_read_tenant


def get_unused_address_objects(actor: User, tenant_id: int) -> tuple[QuerySet[Address], QuerySet[AddressGroup]]:
    """
    Return address objects owned by the given tenant that are not used in any rules.

    An address is considered used if it is:
    - directly referenced by a RuleMatch, or
    - included in an address group owned by the same tenant, where that group
      is referenced by a RuleMatch.
    """
    require_read_tenant(actor, tenant_id)

    address_ct = ContentType.objects.get_for_model(Address)
    address_group_ct = ContentType.objects.get_for_model(AddressGroup)

    used_address_matches = RuleMatch.objects.filter(
        object_type=address_ct,
        object_id=OuterRef("pk"),
    )

    used_address_group_matches = RuleMatch.objects.filter(
        object_type=address_group_ct,
        object_id=OuterRef("pk"),
    )

    used_group_ids = RuleMatch.objects.filter(
        object_type=address_group_ct,
    ).values("object_id")

    used_group_memberships = AddressGroupMember.objects.filter(
        address_id=OuterRef("pk"),
        group__tenant_id=tenant_id,
        group_id__in=used_group_ids,
    )

    unused_addresses = (
        Address.objects.filter(tenant_id=tenant_id)
        .annotate(
            is_directly_used=Exists(used_address_matches),
            is_used_via_group=Exists(used_group_memberships),
        )
        .filter(
            is_directly_used=False,
            is_used_via_group=False,
        )
    )

    unused_address_groups = (
        AddressGroup.objects.filter(tenant_id=tenant_id)
        .annotate(is_used=Exists(used_address_group_matches))
        .filter(is_used=False)
    )

    return unused_addresses, unused_address_groups


def get_unused_service_objects(actor: User, tenant_id: int) -> tuple[QuerySet[Service], QuerySet[ServiceGroup]]:
    """
    Return service objects owned by the given tenant that are not used in any rules.

    A service is considered used if it is:
    - directly referenced by a RuleMatch, or
    - included in a service group owned by the same tenant, where that group
        is referenced by a RuleMatch.
    """
    require_read_tenant(actor, tenant_id)

    service_ct = ContentType.objects.get_for_model(Service)
    service_group_ct = ContentType.objects.get_for_model(ServiceGroup)

    used_service_matches = RuleMatch.objects.filter(
        object_type=service_ct,
        object_id=OuterRef("pk"),
    )

    used_service_group_matches = RuleMatch.objects.filter(
        object_type=service_group_ct,
        object_id=OuterRef("pk"),
    )

    used_group_ids = RuleMatch.objects.filter(
        object_type=service_group_ct,
    ).values("object_id")

    used_group_memberships = ServiceGroupMember.objects.filter(
        service_id=OuterRef("pk"),
        group__tenant_id=tenant_id,
        group_id__in=used_group_ids,
    )

    unused_services = (
        Service.objects.filter(tenant_id=tenant_id)
        .annotate(
            is_directly_used=Exists(used_service_matches),
            is_used_via_group=Exists(used_group_memberships),
        )
        .filter(
            is_directly_used=False,
            is_used_via_group=False,
        )
    )

    unused_service_groups = (
        ServiceGroup.objects.filter(tenant_id=tenant_id)
        .annotate(is_used=Exists(used_service_group_matches))
        .filter(is_used=False)
    )

    return unused_services, unused_service_groups


def get_unused_tag_objects(actor: User, tenant_id: int) -> QuerySet[Tag]:
    """
    Return tag objects owned by the given tenant that don't tag any objects.
    """
    require_read_tenant(actor, tenant_id)
    unused_tags = (
        Tag.objects.filter(tenant_id=tenant_id)
        .annotate(
            is_used=Exists(
                TagConnection.objects.filter(
                    tag_id=OuterRef("pk"),
                )
            )
        )
        .filter(is_used=False)
    )
    return unused_tags


def get_unused_filters(actor: User, tenant_id: int) -> QuerySet[Filter]:
    """
    Return filter objects owned by the given tenant that are not applied to any interfaces
    """
    require_read_tenant(actor, tenant_id)
    unused_filters = (
        Filter.objects.filter(tenant_id=tenant_id)
        .annotate(
            is_used=Exists(
                FilterInterface.objects.filter(
                    filter_id=OuterRef("pk"),
                )
            )
        )
        .filter(is_used=False)
    )
    return unused_filters
