from django.urls import reverse


def get_management_toolbar_context(active_tool):
    if active_tool == "tenants":
        add_button_label = "Add Tenant"
        object_type = "tenants"
    else:
        add_button_label = "Add User"
        object_type = "users"

    return {
        "active_tool": active_tool,
        "toggle_target": "#management-content",
        "toggle_items": [
            {
                "key": "users",
                "label": "User management",
                "url": reverse("management-users"),
            },
            {
                "key": "tenants",
                "label": "Tenant management",
                "url": reverse("management-tenants"),
            },
        ],
        "add_button_label": add_button_label,
        "object_type": object_type,
    }
