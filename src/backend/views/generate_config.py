import zipfile
from io import BytesIO

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse

from backend.objects.tenant_objects.device import Device
from backend.objects.tenant_objects.interface_direction import InterfaceDirection
from backend.services.config_generation.generate_interface_config import (
    generate_interface_config_results,
)
from backend.utils.logger import set_up_logger

logger = set_up_logger(__name__)


def _sanitize_zip_name(name: str, *, fallback: str) -> str:
    if not isinstance(name, str):
        return fallback

    sanitized = name.strip().replace("\\", "_").replace("/", "_").replace("\r", "").replace("\n", "").replace(" ", "_")
    return sanitized or fallback


def _normalize_generated_config_files(config: object, *, fallback_name: str) -> dict[str, str]:
    if config is None:
        return {}

    if isinstance(config, str):
        return {fallback_name: config}

    items_method = getattr(config, "items", None)
    if callable(items_method):
        normalized: dict[str, str] = {}

        try:
            for filename, content in items_method():
                if not isinstance(filename, str) or not filename.strip():
                    logger.warning("Skipping generated config entry with invalid filename: %r", filename)
                    continue

                if not isinstance(content, str):
                    logger.warning(
                        "Skipping generated config entry for filename %r because content is not a string: %r",
                        filename,
                        type(content),
                    )
                    continue

                safe_filename = _sanitize_zip_name(filename, fallback=fallback_name)
                normalized[safe_filename] = content

            return normalized
        except Exception:
            logger.exception("Failed to normalize generated config files for type %r", type(config))
            return {}

    logger.warning("Unsupported generated config type: %r", type(config))
    return {}


def _extract_single_generated_file(config: object, *, fallback_name: str) -> tuple[str, str] | None:
    files = _normalize_generated_config_files(config, fallback_name=fallback_name)

    if not files:
        return None

    if len(files) > 1:
        raise ValueError(f"Expected at most one generated file, but got {len(files)}: {list(files.keys())}")

    return next(iter(files.items()))


def _get_filename_extension(filename: str, *, fallback: str = ".txt") -> str:
    if not isinstance(filename, str):
        return fallback

    if "." not in filename:
        return fallback

    _, ext = filename.rsplit(".", 1)
    ext = ext.strip()
    return f".{ext}" if ext else fallback


@login_required(login_url="login")
def check_interface_config_generation(request, interface_id):
    tenant_id = request.session.get("current_tenant_id")
    if not tenant_id:
        return JsonResponse(
            {
                "status": "error",
                "errors": ["No tenant selected."],
                "warnings": [],
                "can_download": False,
                "download_url": None,
            },
            status=400,
        )

    try:
        tenant_id = int(tenant_id)
    except (TypeError, ValueError):
        return JsonResponse(
            {
                "status": "error",
                "errors": ["Invalid tenant selected."],
                "warnings": [],
                "can_download": False,
                "download_url": None,
            },
            status=400,
        )

    result = generate_interface_config_results(
        actor=request.user,
        tenant_id=tenant_id,
        interface_id=interface_id,
    )

    return JsonResponse(
        {
            "status": result.status,
            "errors": result.all_errors(),
            "warnings": result.all_warnings(),
            "can_download": not result.has_errors,
            "download_url": (f"/devices/interfaces/{interface_id}/download-config/" if not result.has_errors else None),
        }
    )


@login_required(login_url="login")
def download_interface_configs(request, interface_id):
    tenant_id = request.session.get("current_tenant_id")
    if not tenant_id:
        return HttpResponse("No tenant selected.", status=400, content_type="text/plain")

    try:
        tenant_id = int(tenant_id)
    except (TypeError, ValueError):
        return HttpResponse("Invalid tenant selected.", status=400, content_type="text/plain")

    result = generate_interface_config_results(
        actor=request.user,
        tenant_id=tenant_id,
        interface_id=interface_id,
    )

    if result.has_errors:
        error_lines = result.all_errors()
        if result.has_warnings:
            error_lines.append("")
            error_lines.append("Warnings:")
            error_lines.extend(result.all_warnings())

        return HttpResponse(
            "\n".join(error_lines) or "Failed to generate config.",
            status=400,
            content_type="text/plain",
        )

    first_interface_direction = (
        InterfaceDirection.objects.select_related("interface").filter(interface_id=interface_id).first()
    )
    interface_name = _sanitize_zip_name(
        getattr(first_interface_direction.interface, "name", "") if first_interface_direction else "",
        fallback=f"interface_{interface_id}",
    )
    device_name = (
        Device.objects.filter(id=first_interface_direction.interface.device_id).first().name
        if first_interface_direction
        else ""
    )

    inbound_file = _extract_single_generated_file(
        result.inbound.config,
        fallback_name="config_in.txt",
    )
    outbound_file = _extract_single_generated_file(
        result.outbound.config,
        fallback_name="config_out.txt",
    )

    zip_buffer = BytesIO()

    with zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zip_file:
        if inbound_file:
            original_filename, content = inbound_file
            ext = _get_filename_extension(original_filename, fallback=".txt")
            zip_file.writestr(f"{interface_name}_in{ext}", content)

        if outbound_file:
            original_filename, content = outbound_file
            ext = _get_filename_extension(original_filename, fallback=".txt")
            zip_file.writestr(f"{interface_name}_out{ext}", content)

        if result.has_warnings:
            zip_file.writestr("warnings.txt", "\n".join(result.all_warnings()))

    zip_buffer.seek(0)

    response = HttpResponse(zip_buffer.getvalue(), content_type="application/zip")
    response["Content-Disposition"] = f'attachment; filename="{device_name}_{interface_name}_configs.zip"'
    return response
