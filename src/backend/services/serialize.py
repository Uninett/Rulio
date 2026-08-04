from typing import Any


def serialize_rule_object(obj: Any, object_type: str) -> dict[str, Any]:
    """
    Convert any selectable object model into one consistent dictionary
    shape for templates and selector logic.
    """
    return {
        "id": obj.id,
        "name": obj.name,
        "object_type": object_type,
        "selector_id": f"{object_type}-{obj.id}",
    }
