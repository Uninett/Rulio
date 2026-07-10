from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.contrib.auth.models import User
from django.urls import reverse

from backend.objects.tenant_objects.tenant import Tenant
from backend.objects.tenant_objects.tenant_user_member import TenantUserMember
from backend.views.management_helpers import get_management_toolbar_context
from backend.utils.logger import set_up_logger

logger = set_up_logger(__name__)


@login_required(login_url="login")
def get_management_tenants(request):
    request.session["active_page"] = "management"
    request.session["management_active_tool"] = "tenants"
    object_type = "tenants"

    return render(
        request,
        "partials/_page_content.html",
        {
            "title": "Tenant management",
            "object_type": object_type,
            "table_data": get_tenants_view(request),
            **get_management_toolbar_context("tenants", add_button_label="Create Tenant"),
        },
    )


def get_tenants_view(request):
    tenants = Tenant.objects.all().order_by("id")

    headers = ["Tenant", "Members", ""]
    rows = []

    for tenant in tenants:
        memberships = TenantUserMember.objects.filter(tenant=tenant).select_related("user").order_by("user__username")

        member_count = memberships.count()

        member_names = [membership.user.username for membership in memberships]
        members_display = ", ".join(member_names)

        rows.append(
            {
                "id": tenant.id,
                "name": tenant.tenant_name,
                "members": members_display,
                "member_count": member_count,
            }
        )

    return {
        "headers": headers,
        "rows": rows,
    }


def get_tenant_modal_context(object_data=None, selected_user_ids=None, error_message=None):
    return {
        "modal_title": "Add Tenant",
        "modal_mode": "add",
        "modal_object_type": "tenants",
        "modal_type": None,
        "modal_supports_types": False,
        "item_type_editable": False,
        "modal_type_labels": {},
        "modal_content_partial": "partials/management/_tenant_form.html",
        "modal_post_url": reverse("post-tenant-view"),
        "modal_target": "#management-content",
        "modal_swap": "outerHTML",
        "modal_refresh_url": reverse("management-tenants"),
        "object_data": object_data or {},
        "user_options": [{"id": user.id, "name": user.username} for user in User.objects.all().order_by("username")],
        "selected_user_ids": [int(user_id) for user_id in (selected_user_ids or [])],
        "selected_group_ids": [],
        "selected_address_ids": [],
        "selected_service_ids": [],
        "error_message": error_message,
    }


@login_required(login_url="login")
def post_tenant_view(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden("Forbidden")

    tenant_name = request.POST.get("tenant_name", "").strip()
    user_ids = request.POST.getlist("user_ids")

    object_data = {
        "tenant_name": tenant_name,
    }

    if not tenant_name:
        return render(
            request,
            "partials/_modal.html",
            get_tenant_modal_context(
                object_data=object_data,
                selected_user_ids=user_ids,
                error_message="Tenant name is required.",
            ),
            status=400,
        )

    if Tenant.objects.filter(tenant_name=tenant_name).exists():
        return render(
            request,
            "partials/_modal.html",
            get_tenant_modal_context(
                object_data=object_data,
                selected_user_ids=user_ids,
                error_message=f"Tenant '{tenant_name}' already exists.",
            ),
            status=400,
        )

    try:
        tenant = Tenant.objects.create(tenant_name=tenant_name)

        for user_id in user_ids:
            TenantUserMember.objects.get_or_create(
                tenant=tenant,
                user_id=int(user_id),
                defaults={"role": TenantUserMember.TenantRole.MEMBER},
            )

        logger.info(f"Tenant created: {tenant.tenant_name}")

    except Exception as e:
        return render(
            request,
            "partials/_modal.html",
            get_tenant_modal_context(
                object_data=object_data,
                selected_user_ids=user_ids,
                error_message=f"Could not create tenant: {e}",
            ),
            status=400,
        )

    request.session["active_page"] = "management"
    request.session["management_active_tool"] = "tenants"

    return render(
        request,
        "partials/_page_content.html",
        {
            "title": "Tenant management",
            "object_type": "tenants",
            "table_data": get_tenants_view(request),
            **get_management_toolbar_context("tenants", add_button_label="Create Tenant"),
        },
    )
