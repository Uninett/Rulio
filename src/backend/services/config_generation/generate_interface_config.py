from dataclasses import dataclass, field
from typing import Any

from django.contrib.auth.models import User

from backend.objects.tenant_objects.filter_interface import FilterInterface
from backend.objects.tenant_objects.interface_direction import InterfaceDirection
from backend.services.config_generation.build import build_policies_for_interface
from backend.services.config_generation.generate_config import generate_multi_policy_config
from backend.utils.logger import set_up_logger

logger = set_up_logger(__name__)


@dataclass
class InterfaceDirectionGenerationResult:
    success: bool = False
    config: Any = None
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


@dataclass
class InterfaceConfigGenerationResult:
    status: str = "error"
    inbound: InterfaceDirectionGenerationResult = field(default_factory=InterfaceDirectionGenerationResult)
    outbound: InterfaceDirectionGenerationResult = field(default_factory=InterfaceDirectionGenerationResult)

    @property
    def has_errors(self) -> bool:
        return bool(self.inbound.errors or self.outbound.errors)

    @property
    def has_warnings(self) -> bool:
        return bool(self.inbound.warnings or self.outbound.warnings)

    def all_errors(self) -> list[str]:
        return [*self.inbound.errors, *self.outbound.errors]

    def all_warnings(self) -> list[str]:
        return [*self.inbound.warnings, *self.outbound.warnings]


def _build_direction_result(
    *, actor: User, tenant_id: int, interface_id: int, direction: str
) -> InterfaceDirectionGenerationResult:
    try:
        policies = build_policies_for_interface(
            actor=actor,
            tenant_id=tenant_id,
            interface_id=interface_id,
            direction=direction,
        )
        config_result = generate_multi_policy_config(policies)

        return InterfaceDirectionGenerationResult(
            success=config_result.success,
            config=config_result.config,
            warnings=[str(warning) for warning in config_result.warnings],
            errors=[str(error) for error in config_result.errors],
        )
    except Exception as exc:
        logger.exception(
            "Failed to generate %s config for interface_id=%s tenant_id=%s",
            direction,
            interface_id,
            tenant_id,
        )
        return InterfaceDirectionGenerationResult(
            success=False,
            config=None,
            warnings=[],
            errors=[f"Failed to generate {direction} config: {exc}"],
        )


def generate_interface_config_results(
    *, actor: User, tenant_id: int, interface_id: int
) -> InterfaceConfigGenerationResult:
    logger.info(
        "Generating interface config for interface_id=%s tenant_id=%s by actor=%s",
        interface_id,
        tenant_id,
        actor.username,
    )

    first_interface_direction = (
        InterfaceDirection.objects.select_related("interface__device")
        .filter(interface_id=interface_id)
        .first()
    )
    interface = first_interface_direction.interface if first_interface_direction else None

    if interface is None:
        logger.error(
            "Interface with id=%s and tenant_id=%s not found",
            interface_id,
            tenant_id,
        )
        error_message = f"Interface with id={interface_id} and tenant_id={tenant_id} not found"
        return InterfaceConfigGenerationResult(
            status="error",
            inbound=InterfaceDirectionGenerationResult(
                success=False,
                config=None,
                warnings=[],
                errors=[error_message],
            ),
            outbound=InterfaceDirectionGenerationResult(
                success=False,
                config=None,
                warnings=[],
                errors=[error_message],
            ),
        )

    interface_tenant_id = interface.device.tenant_id

    if interface_tenant_id != tenant_id and not actor.is_superuser:
        logger.error(
            "Interface with id=%s belongs to tenant_id=%s, but request was made for tenant_id=%s",
            interface_id,
            interface_tenant_id,
            tenant_id,
        )
        error_message = (
            f"Interface with id={interface_id} belongs to tenant_id={interface_tenant_id}, "
            f"but request was made for tenant_id={tenant_id}"
        )
        return InterfaceConfigGenerationResult(
            status="error",
            inbound=InterfaceDirectionGenerationResult(
                success=False,
                config=None,
                warnings=[],
                errors=[error_message],
            ),
            outbound=InterfaceDirectionGenerationResult(
                success=False,
                config=None,
                warnings=[],
                errors=[error_message],
            ),
        )

    interface_in = InterfaceDirection.objects.filter(interface=interface, direction="in").first()
    interface_out = InterfaceDirection.objects.filter(interface=interface, direction="out").first()

    if interface_in is None or interface_out is None:
        logger.error(
            "Interface with id=%s and tenant_id=%s not found or does not have both directions",
            interface_id,
            tenant_id,
        )
        error_message = (
            f"Interface with id={interface_id} and tenant_id={tenant_id} "
            "not found or does not have both directions"
        )
        return InterfaceConfigGenerationResult(
            status="error",
            inbound=InterfaceDirectionGenerationResult(
                success=False,
                config=None,
                warnings=[],
                errors=[error_message],
            ),
            outbound=InterfaceDirectionGenerationResult(
                success=False,
                config=None,
                warnings=[],
                errors=[error_message],
            ),
        )

    filters_on_interface_in = FilterInterface.objects.filter(
        interface_direction_id=interface_in.id
    ).exists()
    filters_on_interface_out = FilterInterface.objects.filter(
        interface_direction_id=interface_out.id
    ).exists()

    if not filters_on_interface_in and not filters_on_interface_out:
        logger.warning(
            "No filters found on interface_id=%s tenant_id=%s for either direction",
            interface_id,
            tenant_id,
        )
        error_message = (
            f"No filters found on interface_id={interface_id} tenant_id={tenant_id} for either direction"
        )
        return InterfaceConfigGenerationResult(
            status="error",
            inbound=InterfaceDirectionGenerationResult(
                success=False,
                config=None,
                warnings=[],
                errors=[error_message],
            ),
            outbound=InterfaceDirectionGenerationResult(
                success=False,
                config=None,
                warnings=[],
                errors=[error_message],
            ),
        )

    if not filters_on_interface_in:
        logger.warning(
            "No filters found on interface_id=%s tenant_id=%s for inbound direction",
            interface_id,
            tenant_id,
        )
        inbound = InterfaceDirectionGenerationResult(
            success=False,
            config=None,
            warnings=[
                f"No filters found on interface_id={interface_id} tenant_id={tenant_id} for inbound direction"
            ],
            errors=[],
        )
    else:
        inbound = _build_direction_result(
            actor=actor,
            tenant_id=tenant_id,
            interface_id=interface_id,
            direction="in",
        )

    if not filters_on_interface_out:
        logger.warning(
            "No filters found on interface_id=%s tenant_id=%s for outbound direction",
            interface_id,
            tenant_id,
        )
        outbound = InterfaceDirectionGenerationResult(
            success=False,
            config=None,
            warnings=[
                f"No filters found on interface_id={interface_id} tenant_id={tenant_id} for outbound direction"
            ],
            errors=[],
        )
    else:
        outbound = _build_direction_result(
            actor=actor,
            tenant_id=tenant_id,
            interface_id=interface_id,
            direction="out",
        )

    result = InterfaceConfigGenerationResult(
        inbound=inbound,
        outbound=outbound,
    )

    if result.has_errors:
        result.status = "error"
    elif result.has_warnings:
        result.status = "success_with_warnings"
    else:
        result.status = "success"

    logger.info(
        "Interface config generation completed for interface_id=%s tenant_id=%s by actor=%s with status=%s",
        interface_id,
        tenant_id,
        actor.username,
        result.status,
    )
    logger.info("Result: %s", serialize_generated_config(result))
    return result


def serialize_generated_config(config: Any) -> str:
    if config is None:
        return ""
    if isinstance(config, str):
        return config
    return str(config)