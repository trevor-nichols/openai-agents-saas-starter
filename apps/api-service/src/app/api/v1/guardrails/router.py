"""Guardrails catalog endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies.auth import CurrentUser, require_verified_scopes
from app.api.v1.guardrails.schemas import (
    GuardrailCheckConfigSchema,
    GuardrailDetail,
    GuardrailSummary,
    PresetDetail,
    PresetSummary,
)
from app.guardrails._shared.registry import get_guardrail_registry

router = APIRouter(prefix="/guardrails", tags=["guardrails"])


@router.get("", response_model=list[GuardrailSummary])
async def list_guardrails(
    _current_user: CurrentUser = Depends(require_verified_scopes("tools:read")),
) -> list[GuardrailSummary]:
    """Return all available guardrail specifications."""
    registry = get_guardrail_registry()
    specs = registry.list_specs()

    return [
        GuardrailSummary(
            key=spec.key,
            display_name=spec.display_name,
            description=spec.description,
            stage=spec.stage,
            engine=spec.engine,
            supports_masking=spec.supports_masking,
        )
        for spec in specs
    ]


@router.get("/presets", response_model=list[PresetSummary])
async def list_presets(
    _current_user: CurrentUser = Depends(require_verified_scopes("tools:read")),
) -> list[PresetSummary]:
    """Return all available guardrail presets."""
    registry = get_guardrail_registry()
    presets = registry.list_presets()

    return [
        PresetSummary(
            key=preset.key,
            display_name=preset.display_name,
            description=preset.description,
            guardrail_count=len(preset.guardrails),
        )
        for preset in presets
    ]


@router.get("/{guardrail_key}", response_model=GuardrailDetail)
async def get_guardrail(
    guardrail_key: str,
    _current_user: CurrentUser = Depends(require_verified_scopes("tools:read")),
) -> GuardrailDetail:
    """Return detailed information about a specific guardrail."""
    registry = get_guardrail_registry()
    spec = registry.get_spec(guardrail_key)

    if spec is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Guardrail '{guardrail_key}' not found",
        )

    return GuardrailDetail(
        key=spec.key,
        display_name=spec.display_name,
        description=spec.description,
        stage=spec.stage,
        engine=spec.engine,
        supports_masking=spec.supports_masking,
        uses_conversation_history=spec.uses_conversation_history,
        tripwire_on_error=spec.tripwire_on_error,
        default_config=spec.default_config,
        config_schema=spec.config_schema.model_json_schema(),
    )


@router.get("/presets/{preset_key}", response_model=PresetDetail)
async def get_preset(
    preset_key: str,
    _current_user: CurrentUser = Depends(require_verified_scopes("tools:read")),
) -> PresetDetail:
    """Return detailed information about a specific preset."""
    registry = get_guardrail_registry()
    preset = registry.get_preset(preset_key)

    if preset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Preset '{preset_key}' not found",
        )

    return PresetDetail(
        key=preset.key,
        display_name=preset.display_name,
        description=preset.description,
        guardrail_count=len(preset.guardrails),
        guardrails=[
            GuardrailCheckConfigSchema(
                guardrail_key=cfg.guardrail_key,
                enabled=cfg.enabled,
                config=cfg.config,
            )
            for cfg in preset.guardrails
        ],
    )
