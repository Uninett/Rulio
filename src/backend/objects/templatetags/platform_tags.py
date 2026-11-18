from django import template

from backend.services.config_generation.platform_capabilities import PLATFORM_VENDORS, get_platform_vendor

register = template.Library()


# The vendor and platform options for the device form, with the device's current platform preselected.
# Every view that renders the form passes the platform in object_data, so the form needs no extra view context.
@register.simple_tag
def device_platform_options(selected_platform):
    selected_platform = (selected_platform or "").strip().lower()
    selected_vendor = get_platform_vendor(selected_platform)

    vendors = [
        {
            "label": vendor,
            "selected": vendor == selected_vendor,
            "platforms": [
                {"key": key, "label": label, "selected": key == selected_platform} for key, label in platforms
            ],
        }
        for vendor, platforms in PLATFORM_VENDORS.items()
    ]
    # The platform dropdown is only needed when the chosen vendor has more than one platform.
    show_platform = selected_vendor is not None and len(PLATFORM_VENDORS[selected_vendor]) > 1
    return {"vendors": vendors, "show_platform": show_platform}
