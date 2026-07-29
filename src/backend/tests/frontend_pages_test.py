import pytest
from django.test import Client


PUBLIC_PAGES = [
    {
        "url": "/login/",
        "expected_text": b"<html",
        "template_name": "login.html",
    },
]

PROTECTED_FULL_PAGES = [
    {
        "url": "/devices/",
        "expected_text": b"devices",
        "template_name": "devices.html",
    },
    {
        "url": "/filters/",
        "expected_text": b"filters",
        "template_name": "filters.html",
    },
    {
        "url": "/objects/",
        "expected_text": b"addresses",
        "template_name": "objects.html",
    },
    {
        "url": "/objects/?object_type=services",
        "expected_text": b"services",
        "template_name": "objects.html",
    },
    {
        "url": "/tags/",
        "expected_text": b"tags",
        "template_name": "tags.html",
    },
    {
        "url": "/management/",
        "expected_text": b"management",
        "template_name": "management.html",
    },
]

PROTECTED_PARTIAL_PAGES = [
    {
        "url": "/management/users/",
        "expected_text": b"user management",
        "template_name": "partials/management/_users_table.html",
    },
    {
        "url": "/management/tenants/",
        "expected_text": b"tenant management",
        "template_name": "partials/management/_tenants_table.html",
    },
]

PROTECTED_REDIRECT_PAGES = [
    "/devices/",
    "/filters/",
    "/objects/",
    "/tags/",
    "/management/",
    "/management/users/",
    "/management/tenants/",
]

OBJECT_MODAL_PAGES = [
    "/modal/add/devices/",
    "/modal/add/filters/",
    "/modal/add/addresses/",
    "/modal/add/services/",
    "/modal/add/tags/",
]

MANAGEMENT_MODAL_PAGES = [
    "/modal/add/users/",
    "/modal/add/tenants/",
]

COMMON_ERROR_KEYWORDS = (
    b"traceback",
    b"server error",
    b"internal server error",
    b"exception at",
    b"templatedoesnotexist",
    b"noreversematch",
    b"attributeerror",
    b"typeerror",
    b"valueerror",
    b"keyerror",
)


def _assert_no_common_error_keywords(response_content: bytes) -> None:
    content = response_content.lower()
    for keyword in COMMON_ERROR_KEYWORDS:
        assert keyword not in content, (
            f"Found error keyword in response: "
            f"{keyword.decode('utf-8', errors='ignore')}"
        )


def _assert_template_used(response, expected_template_name: str) -> None:
    used_templates = [template.name for template in response.templates if template.name]
    assert expected_template_name in used_templates, (
        f"Expected template '{expected_template_name}' to be used, "
        f"but got {used_templates}"
    )


def _assert_basic_full_page_health(response, expected_text: bytes | None = None) -> None:
    assert response.status_code == 200
    assert response.content

    content = response.content.lower()
    _assert_no_common_error_keywords(content)

    assert b"<html" in content or b"<main>" in content

    if expected_text is not None:
        assert expected_text in content


def _assert_basic_partial_page_health(response, expected_text: bytes | None = None) -> None:
    assert response.status_code == 200
    assert response.content

    content = response.content.lower()
    _assert_no_common_error_keywords(content)

    assert b"<div" in content or b"<section" in content or b"<form" in content

    if expected_text is not None:
        assert expected_text in content


def _assert_basic_modal_health(response) -> None:
    assert response.status_code == 200
    assert response.content

    content = response.content.lower()
    _assert_no_common_error_keywords(content)

    assert (
        b"modal" in content
        or b"form" in content
        or b"hx-" in content
    ), "Expected modal/form fragment content to be present"


@pytest.mark.django_db
@pytest.mark.parametrize("page", PUBLIC_PAGES)
def test_public_pages_load(page):
    client = Client()
    response = client.get(page["url"], follow=True)

    _assert_basic_full_page_health(response, page["expected_text"])
    _assert_template_used(response, page["template_name"])


@pytest.mark.django_db
@pytest.mark.parametrize("url", PROTECTED_REDIRECT_PAGES)
def test_protected_pages_require_login(url):
    client = Client()
    response = client.get(url, follow=False)

    assert response.status_code == 302
    assert "/login/" in response.url


@pytest.mark.django_db
@pytest.mark.parametrize("page", PROTECTED_FULL_PAGES)
def test_authenticated_full_frontend_pages_load(authenticated_client_with_tenant, page):
    response = authenticated_client_with_tenant.get(page["url"], follow=True)

    _assert_basic_full_page_health(response, page["expected_text"])
    _assert_template_used(response, page["template_name"])


@pytest.mark.django_db
@pytest.mark.parametrize("page", PROTECTED_PARTIAL_PAGES)
def test_authenticated_partial_frontend_pages_load(authenticated_client_with_tenant, page):
    response = authenticated_client_with_tenant.get(page["url"], follow=True)

    _assert_basic_partial_page_health(response, page["expected_text"])
    _assert_template_used(response, page["template_name"])


@pytest.mark.django_db
@pytest.mark.parametrize("url", OBJECT_MODAL_PAGES)
def test_object_modal_pages_load(authenticated_client_with_tenant, url):
    response = authenticated_client_with_tenant.get(url, follow=True)

    _assert_basic_modal_health(response)


@pytest.mark.django_db
@pytest.mark.parametrize("url", MANAGEMENT_MODAL_PAGES)
def test_management_modal_pages_load(authenticated_client_with_tenant, url):
    response = authenticated_client_with_tenant.get(url, follow=True)

    _assert_basic_modal_health(response)
