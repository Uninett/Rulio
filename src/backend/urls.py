"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path


from .api import (
    api,
)

from .views.session import (
    get_login_page,
    logout_view,
    set_tenant_view,
)

from .views.management_page import (
    get_management_page,
)

from .views.management_users import get_management_users, post_user_view, update_user_view, delete_user_view
from .views.management_tenants import get_management_tenants, post_tenant_view, update_tenant_view, delete_tenant_view

from .views.devices_page import (
    get_devices_page,
)

from .views.filters_page import (
    get_filters_page,
    update_filter_view,
    post_filter_view,
    get_filters_content,
    delete_filter_view,
)

from .views.objects_page import (
    get_objects_page,
)

from .views.objects_addresses import (
    get_objects_addresses,
    post_address_view,
    update_address_view,
    delete_address_view,
)

from .views.objects_address_groups import (
    post_address_group_view,
    update_address_group_view,
    delete_address_group_view,
)

from .views.objects_services import (
    get_objects_services,
    post_service_view,
    update_service_view,
    delete_service_view,
)

from .views.objects_service_groups import (
    post_service_group_view,
    update_service_group_view,
    delete_service_group_view,
)

from backend.views.rule_page import (
    delete_rule_view,
    get_rule_page,
    get_rules_content,
    get_rule_selector_modal,
    post_rule_view,
    reorder_rule_view,
    update_rule_view,
)

from .views.tags_page import (
    get_tags_page,
    post_tag_view,
    update_tag_view,
    delete_tag_view,
)

from .views.modal_add import (
    get_add_modal,
    get_add_modal_form_content,
)

from .views.modal_update import (
    get_update_modal,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", api.urls),
    path("login/", get_login_page, name="login"),
    path("logout/", logout_view, name="logout"),
    path("set-tenant/", set_tenant_view, name="set-tenant"),
    # Management
    path("management/", get_management_page, name="management-page"),
    path("management/users/", get_management_users, name="management-users"),
    path("management/users/create/", post_user_view, name="post-user-view"),
    path("management/users/<int:object_id>/update/", update_user_view, name="update-user-view"),
    path("management/users/<int:object_id>/delete/", delete_user_view, name="delete-user-view"),
    path("management/tenants/", get_management_tenants, name="management-tenants"),
    path("management/tenants/create/", post_tenant_view, name="post-tenant-view"),
    path("management/tenants/<int:object_id>/update/", update_tenant_view, name="update-tenant-view"),
    path("management/tenants/<int:object_id>/delete/", delete_tenant_view, name="delete-tenant-view"),
    # Device Page
    path("devices/", get_devices_page, name="devices"),
    # Filters Page
    path("filters/", get_filters_page, name="filters"),
    path("filters/create/", post_filter_view, name="post-filter-view"),
    path("filters/<int:object_id>/update/", update_filter_view, name="update-filter-view"),
    path("filters/content/", get_filters_content, name="filters-content"),
    path("filters/<int:object_id>/delete/", delete_filter_view, name="delete-filter-view"),
    # Objects Page: Address
    path("objects/", get_objects_page, name="objects"),
    path("objects/addresses/", get_objects_addresses, name="objects-addresses"),
    path("addresses/create/", post_address_view, name="post-address-view"),
    path("addresses/<int:object_id>/update/", update_address_view, name="update-address-view"),
    path("addresses/<int:object_id>/delete/", delete_address_view, name="delete-address-view"),
    path("address-groups/create/", post_address_group_view, name="post-address-group-view"),
    path("address-groups/<int:object_id>/update/", update_address_group_view, name="update-address-group-view"),
    path("address-groups/<int:object_id>/delete/", delete_address_group_view, name="delete-address-group-view"),
    # Objects Page: Service
    path("objects/services/", get_objects_services, name="objects-services"),
    path("services/create/", post_service_view, name="post-service-view"),
    path("services/<int:object_id>/update/", update_service_view, name="update-service-view"),
    path("services/<int:object_id>/delete/", delete_service_view, name="delete-service-view"),
    path("service-groups/create/", post_service_group_view, name="post-service-group-view"),
    path("service-groups/<int:object_id>/update/", update_service_group_view, name="update-service-group-view"),
    path("service-groups/<int:object_id>/delete/", delete_service_group_view, name="delete-service-group-view"),
    # Tags Page
    path("tags/", get_tags_page, name="tags"),
    path("tags/create/", post_tag_view, name="post-tag-view"),
    path("tags/<int:object_id>/update/", update_tag_view, name="update-tag-view"),
    path("tags/<int:object_id>/delete/", delete_tag_view, name="delete-tag-view"),
    # Modal Partial
    path("modal/add/<str:object_type>/", get_add_modal, name="modal-add"),
    path("modal/add/<str:object_type>/<str:type>/form/", get_add_modal_form_content, name="modal-add-form-content"),
    path("modal/update/<str:row_id>/", get_update_modal, name="modal-update"),
    path("modal/rule-selector/<str:selector_type>/", get_rule_selector_modal, name="rule-selector-modal"),
    path("rules/", get_rule_page, name="rules-page"),
    path("rules/content/", get_rules_content, name="rules-content"),
    path("rules/create/", post_rule_view, name="post-rule-view"),
    path("rules/reorder/", reorder_rule_view, name="reorder-rule-view"),
    path("rules/<int:rule_id>/update/", update_rule_view, name="update-rule-view"),
    path("rules/<int:rule_id>/delete/", delete_rule_view, name="delete-rule-view"),
]
