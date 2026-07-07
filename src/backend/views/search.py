from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required(login_url="login")
def get_search_results(request):
    object_type = "search"
    return render(
        request,
        "partials/_page_content.html",
        {
            "object_type": object_type,
            "search_results": get_search_view(request),  # Address data for the page
        },
    )


def get_search_view(request):
    return {
        "results": ["Devices", "Filters", "Objects", "Tags"],
    }
