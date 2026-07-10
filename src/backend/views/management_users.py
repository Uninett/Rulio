from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import render

from backend.objects.tenant_objects.tenant import Tenant
from backend.objects.tenant_objects.tenant_user_member import TenantUserMember
from backend.utils.logger import set_up_logger
from backend.views.management_helpers import get_management_toolbar_context

logger = set_up_logger(__name__)


@login_required(login_url="login")
def get_management_users(request):
    request.session["active_page"] = "management"
    request.session["management_active_tool"] = "users"
    object_type = "users"

    return render(
        request,
        "partials/_page_content.html",
        {
            "title": "User management",
            "object_type": object_type,
            "table_data": get_users_view(request),
            **get_management_toolbar_context("users", add_button_label="Create User"),
        },
    )


def get_users_view(request):
    headers = ["Username", "Last login", "Date joined", ""]
    rows = []

    for user in User.objects.all().order_by("username"):
        rows.append(
            {
                "id": user.id,
                "row_id": f"user-{user.id}",
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "is_superuser": user.is_superuser,
                "last_login": user.last_login,
                "date_joined": user.date_joined,
            }
        )

    return {
        "headers": headers,
        "rows": rows,
    }


def get_user_modal_context(object_data=None, selected_permissions=None, error_message=None):
    return {
        "modal_title": "Add User",
        "modal_mode": "add",
        "modal_object_type": "users",
        "modal_type": None,
        "modal_supports_types": False,
        "item_type_editable": False,
        "modal_type_labels": {},
        "modal_content_partial": "partials/management/_user_form.html",
        "modal_post_url": reverse("post-user-view"),
        "modal_target": "#management-content",
        "modal_swap": "innerHTML",
        "modal_refresh_url": reverse("management-users"),
        "object_data": object_data or {},
        "tenant_options": [
            {"id": tenant.id, "name": tenant.tenant_name}
            for tenant in Tenant.objects.exclude(id=1).order_by("tenant_name")
        ],
        "selected_permissions": selected_permissions or [],
        "selected_group_ids": [],
        "selected_address_ids": [],
        "selected_service_ids": [],
        "error_message": error_message,
    }


@login_required(login_url="login")
def post_user_view(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden("Forbidden")

    username = request.POST.get("username", "").strip()
    first_name = request.POST.get("first_name", "").strip()
    last_name = request.POST.get("last_name", "").strip()
    email = request.POST.get("email", "").strip()
    password = request.POST.get("password", "")
    tenant_id = request.POST.get("tenant_id", "").strip()
    is_superuser = request.POST.get("is_superuser") == "on"

    object_data = {
        "username": username,
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "tenant_id": tenant_id,
        "is_superuser": is_superuser,
    }

    if not username:
        return render(
            request,
            "partials/_modal.html",
            get_user_modal_context(
                object_data=object_data,
                error_message="Username is required.",
            ),
            status=400,
        )

    if not password:
        return render(
            request,
            "partials/_modal.html",
            get_user_modal_context(
                object_data=object_data,
                error_message="Password is required.",
            ),
            status=400,
        )

    if User.objects.filter(username=username).exists():
        return render(
            request,
            "partials/_modal.html",
            get_user_modal_context(
                object_data=object_data,
                error_message=f"User with username '{username}' already exists.",
            ),
            status=400,
        )

    try:
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
        )
        user.first_name = first_name
        user.last_name = last_name
        user.is_superuser = is_superuser
        user.is_staff = is_superuser
        user.save()

        global_role = TenantUserMember.TenantRole.ADMIN if is_superuser else TenantUserMember.TenantRole.MEMBER

        TenantUserMember.objects.get_or_create(
            user=user,
            tenant_id=1,
            defaults={"role": global_role},
        )

        if not is_superuser and tenant_id:
            TenantUserMember.objects.get_or_create(
                user=user,
                tenant_id=int(tenant_id),
                defaults={"role": TenantUserMember.TenantRole.MEMBER},
            )

        logger.info(f"User created: {user.username}")

    except Exception as e:
        return render(
            request,
            "partials/_modal.html",
            get_user_modal_context(
                object_data=object_data,
                error_message=f"Could not create user: {e}",
            ),
            status=400,
        )

    request.session["active_page"] = "management"
    request.session["management_active_tool"] = "users"

    return render(
        request,
        "partials/_page_content.html",
        {
            "title": "User management",
            "object_type": "users",
            "table_data": get_users_view(request),
            **get_management_toolbar_context("users", add_button_label="Create User"),
        },
    )


@login_required(login_url="login")
def update_user_view(request, object_id):
    if not request.user.is_superuser:
        return HttpResponseForbidden("Forbidden")

    user = User.objects.filter(id=object_id).first()
    if not user:
        return HttpResponse("User not found.", status=404)

    first_name = request.POST.get("first_name", "").strip()
    last_name = request.POST.get("last_name", "").strip()
    email = request.POST.get("email", "").strip()
    password = request.POST.get("password", "").strip()
    is_superuser = request.POST.get("is_superuser") == "on"

    try:
        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.is_superuser = is_superuser
        user.is_staff = is_superuser
        if password:
            user.set_password(password)

        user.save()
    except Exception as e:
        return HttpResponse(f"Could not update user: {e}", status=400)

    return HttpResponse(status=204)
