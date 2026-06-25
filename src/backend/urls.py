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

from .views import (
    set_selected_tenant,
    get_devices_page,
    get_filters_page,
    get_objects_page,
    get_tags_page,
    get_objects_addresses,
    post_address_view,
    get_objects_services,
    post_service_view,
    get_add_modal,
    get_add_modal_form_content,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", api.urls),
    # Tenant
    path("set-tenant/", set_selected_tenant, name="set-tenant"),
    # Device Page
    path("devices/", get_devices_page, name="devices"),
    # Filters Page
    path("filters/", get_filters_page, name="filters"),
    # Objects Page: Address
    path("objects/", get_objects_page, name="objects"),
    path("objects/addresses/", get_objects_addresses, name="objects-addresses"),
    path("addresses/create/", post_address_view, name="post-address-view"),
    # Objects Page: Service
    path("objects/services/", get_objects_services, name="objects-services"),
    path("services/create/", post_service_view, name="post-service-view"),
    # Tags Page
    path("tags/", get_tags_page, name="tags"),
    # Modal Partial
    path("modal/add/<str:object_type>/", get_add_modal, name="modal-add"),
    path("modal/add/<str:object_type>/<str:type>/form/", get_add_modal_form_content, name="modal-add-form-content"),
]
