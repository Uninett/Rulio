from django.urls import reverse


def get_management_toolbar_context(active_tool):
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
    }
