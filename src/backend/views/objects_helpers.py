from django.urls import reverse


# Build shared toolbar context for the Objects page tabs.
def get_objects_toolbar_context(active_tool, add_button_label="Add Address"):
    return {
        "active_tool": active_tool,
        "toggle_target": "#objects-content",
        "toggle_items": [
            {
                "key": "addresses",
                "label": "Addresses",
                "url": reverse("objects-addresses"),
            },
            {
                "key": "services",
                "label": "Services",
                "url": reverse("objects-services"),
            },
        ],
        "add_button_label": add_button_label,
    }
