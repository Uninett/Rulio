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
from django.views.generic import TemplateView

from .api import (
    api,
    devices,
    filters,
    tags,
    addresses,
    addresses_show_all,
    addresses_global,
    addresses_local,
    services,
    services_show_all,
    services_global,
    services_local,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", api.urls),
    path("devices/", devices, name="devices"),
    path("filters/", filters, name="filters"),
    path("tags/", tags, name="tags"),
    path("addresses/", addresses, name="addresses"),
    path("addresses/show-all/", addresses_show_all, name="addresses-show-all"),
    path("addresses/global/", addresses_global, name="addresses-global"),
    path("addresses/local/", addresses_local, name="addresses-local"),
    path("services/", services, name="services"),
    path("services/show-all/", services_show_all, name="services-show-all"),
    path("services/global/", services_global, name="services-global"),
    path("services/local/", services_local, name="services-local"),
]
