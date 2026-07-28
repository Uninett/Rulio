
from django.contrib.auth.models import User
from django.db.models import Exists, OuterRef, QuerySet
from django.contrib.contenttypes.models import ContentType

from backend.objects.attributes.address import Address
from backend.objects.attributes.address_group import AddressGroup
from backend.objects.attributes.address_group_member import AddressGroupMember
from backend.objects.attributes.service import Service
from backend.objects.attributes.service_group import ServiceGroup
from backend.objects.attributes.service_group_member import ServiceGroupMember
from backend.objects.attributes.tag import Tag
from backend.objects.attributes.tag_connection import TagConnection
from backend.objects.filters.rule_match import RuleMatch
from backend.services.helper_user_tenant import require_read_tenant


def get_unused_address_objects(
    actor: User, tenant_id: int
) -> tuple[QuerySet[Address], QuerySet[AddressGroup]]:
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
        