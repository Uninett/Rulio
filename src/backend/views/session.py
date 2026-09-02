from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import redirect, render

from backend.objects.tenant_objects.tenant import Tenant
from backend.objects.tenant_objects.tenant_user_member import TenantUserMember
from backend.services.helper_user_tenant import can_write_tenant, is_superadmin
from constants import GLOBAL_TENANT_ID

"""
====================================================================
Login Page
====================================================================
"""


def get_login_page(request):
    if request.user.is_authenticated:
        return redirect(request.session.get("active_page", "devices"))

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        user = authenticate(request, username=username, password=password)

        if user is None:
            return render(
                request,
                "login.html",
                {
                    "error": "Invalid username or password",
                },
                status=401,
            )

        login(request, user)
        request.session["active_page"] = "devices"

        if user.is_superuser:
            # Set the first tenant as the current tenant for superusers as default.
            first_tenant = Tenant.objects.first()
            if first_tenant:
                request.session["current_tenant_id"] = first_tenant.id
        else:
            # Set the current tenant for non-superusers based on their non-global membership first.
            tenant_member = TenantUserMember.objects.filter(user_id=user.id).exclude(tenant_id=GLOBAL_TENANT_ID).first()

            if tenant_member:
                request.session["current_tenant_id"] = tenant_member.tenant_id
            else:
                global_member = TenantUserMember.objects.filter(
                    user_id=user.id,
                    tenant_id=GLOBAL_TENANT_ID,
                ).first()
                if global_member:
                    request.session["current_tenant_id"] = global_member.tenant_id

        return redirect("devices")

    return render(
        request,
        "login.html",
    )


# Remove the current tenant from the session and log out the user, then redirect to the login page.
@login_required(login_url="login")
def logout_view(request):
    if request.method == "POST":
        request.session.pop("current_tenant_id", None)
        request.session.pop("active_page", None)
        logout(request)
        return redirect("login")

    return redirect("login")


"""
====================================================================
Tenant
====================================================================
"""


# Gets the list of tenants from the backend
def get_tenants_view(request):
    if is_superadmin(request.user):
        tenants = Tenant.objects.all().order_by("id")
    else:
        tenant_ids = list(TenantUserMember.objects.filter(user=request.user).values_list("tenant_id", flat=True))

        if GLOBAL_TENANT_ID in tenant_ids:
            tenant_ids.remove(GLOBAL_TENANT_ID)

        tenants = Tenant.objects.filter(id__in=tenant_ids).order_by("id")

    return [
        {
            "id": tenant.id,
            "name": tenant.tenant_name,
        }
        for tenant in tenants
    ]


# Builds the data that the templates need in order to render the tenant dropdown correctly
def get_tenant_context(request):
    selected_tenant = request.session.get("current_tenant_id")

    can_write_current_tenant = False
    if selected_tenant:
        try:
            can_write_current_tenant = can_write_tenant(request.user, int(selected_tenant))
        except Exception:
            can_write_current_tenant = False

    return {
        "tenants": get_tenants_view(request),
        "selected_tenant": selected_tenant,
        "can_write_current_tenant": can_write_current_tenant,
    }


# Handles setting the current tenant in the session based on the selected tenant from the dropdown.
@login_required(login_url="login")
def set_tenant_view(request):
    if request.method != "POST":
        return redirect(request.session.get("active_page", "devices"))

    tenant_id = request.POST.get("tenant_id")

    if not tenant_id:
        return HttpResponse("Missing tenant_id", status=400)

    try:
        tenant = Tenant.objects.get(id=tenant_id)
    except Tenant.DoesNotExist:
        return HttpResponse(f"Tenant with id {tenant_id} does not exist.", status=404)

    request.session["current_tenant_id"] = tenant.id
    request.session.modified = True

    return HttpResponse(status=204)
