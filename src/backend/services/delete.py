from backend.utils.logger import set_up_logger
from backend.objects.attributes.mixin.taggable_mixin import TaggableMixin
from backend.services.get import get_object_by_type_and_id
from backend.objects.attributes.tag import Tag
from backend.objects.filters.rule import Rule


logger = set_up_logger(__name__)


def clear_all_tags_from_object(object_id: int, object_type: str) -> int:

    obj = get_object_by_type_and_id(object_type, object_id)
    if not isinstance(obj, TaggableMixin):
        raise ValueError(f"Object of type {object_type} does not support tagging.")

    deleted_count = obj.clear_tags()
    logger.info(f"Cleared {deleted_count} tags from {object_type} with id={object_id}.")
    return deleted_count


def remove_tag_from_object(object_id: int, object_type: str, tag_id: int) -> int:

    obj = get_object_by_type_and_id(object_type, object_id)
    if not isinstance(obj, TaggableMixin):
        raise ValueError(f"Object of type {object_type} does not support tagging.")

    from backend.objects.attributes.tag import Tag

    try:
        tag = Tag.objects.get(id=tag_id)
    except Tag.DoesNotExist:
        raise ValueError(f"Tag with id={tag_id} does not exist.")

    deleted_count = obj.remove_tag(tag)
    logger.info(
        f"Removed tag id={tag_id} from {object_type} with id={object_id}. Deleted connections: {deleted_count}."
    )
    return deleted_count


def delete_tag_from_tenant(tag_id: int, tenant_id: int) -> int:
    try:
        tag = Tag.objects.get(id=tag_id, tenant_id=tenant_id)
    except Tag.DoesNotExist:
        raise ValueError(f"Tag with id={tag_id} does not exist in tenant={tenant_id}.")

    deleted_count, _ = tag.delete()
    logger.info(f"Deleted tag id={tag_id} from tenant={tenant_id}. Deleted connections: {deleted_count}.")
    return deleted_count

def delete_rule(rule_id: int, tenant_id: int) -> None:
    try:
        rule = Rule.objects.get(id=rule_id, tenant_id=tenant_id)
    except Rule.DoesNotExist:
        raise ValueError(f"Rule with id={rule_id} does not exist in tenant={tenant_id}.")

    rule.delete()
    logger.info(f"Deleted rule id={rule_id} from tenant={tenant_id}.")
