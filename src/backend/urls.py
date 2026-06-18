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
    addresses_content,
    services,
    services_content,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", api.urls),
    path("devices/", devices, name="devices"),
    path("filters/", filters, name="filters"),
    path("tags/", tags, name="tags"),
    path("addresses/", addresses, name="addresses"),
    path("addresses/content/", addresses_content, name="addresses-content"),
    path("services/", services, name="services"),
    path("services/content/", services_content, name="services-content"),
]
