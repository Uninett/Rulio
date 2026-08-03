from dataclasses import dataclass, field
from typing import Any

from django.contrib.auth.models import User

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
    inbound = _build_direction_result(
        actor=actor,
        tenant_id=tenant_id,
        interface_id=interface_id,
        direction="in",
    )
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
    return result


def serialize_generated_config(config: Any) -> str:
    if config is None:
        return ""
    if isinstance(config, str):
        return config
    return str(config)
