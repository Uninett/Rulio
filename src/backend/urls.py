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
    get_devices_page,
    get_filters_page,
    get_objects_page,
    get_tags_page,
    get_empty_address_row_partial,
    post_address_row_partial,
    get_objects_addresses,
    get_objects_services,
    get_add_modal,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", api.urls),
    path("devices/", get_devices_page, name="devices"),
    path("filters/", get_filters_page, name="filters"),
    path("objects/", get_objects_page, name="objects"),
    path("addresses/new/", get_empty_address_row_partial, name="new-address-row"),
    path("addresses/save/", post_address_row_partial, name="save_address_row"),
    path("objects/addresses/", get_objects_addresses, name="objects-addresses"),
    path("objects/services/", get_objects_services, name="objects-services"),
    path("tags/", get_tags_page, name="tags"),
    path("modal/add/<str:object_type>/", get_add_modal, name="modal-add"),
]
