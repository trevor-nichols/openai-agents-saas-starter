"""Asset seeding helpers."""

from __future__ import annotations

from collections.abc import Callable
from uuid import NAMESPACE_URL, uuid5

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import Settings
from app.domain.storage import StorageProviderProtocol
from app.infrastructure.persistence.assets.models import AgentAsset
from app.infrastructure.persistence.storage.models import StorageBucket, StorageObject
from app.infrastructure.persistence.tenants.models import TenantAccount
from app.services.storage.naming import (
    bucket_name,
    bucket_region,
    safe_filename,
    should_auto_create_bucket,
)
from app.services.test_fixtures.errors import TestFixtureError
from app.services.test_fixtures.schemas import (
    FixtureAsset,
    FixtureAssetResult,
    FixtureConversationResult,
    FixtureUserResult,
)
from app.services.test_fixtures.seeders.resolve import resolve_conversation_id, resolve_user_id


async def ensure_assets(
    session: AsyncSession,
    tenant: TenantAccount,
    user_results: dict[str, FixtureUserResult],
    conversation_results: dict[str, FixtureConversationResult],
    assets: list[FixtureAsset],
    *,
    settings_provider: Callable[[], Settings],
    storage_provider_resolver: Callable[[Settings], StorageProviderProtocol],
) -> dict[str, FixtureAssetResult]:
    if not assets:
        return {}

    settings = settings_provider()
    provider = storage_provider_resolver(settings)
    bucket_name_value = bucket_name(settings, tenant.id)
    region = bucket_region(settings)
    await provider.ensure_bucket(
        bucket_name_value,
        region=region,
        create_if_missing=should_auto_create_bucket(settings),
    )

    bucket = await session.scalar(
        select(StorageBucket).where(
            StorageBucket.tenant_id == tenant.id,
            StorageBucket.bucket_name == bucket_name_value,
        )
    )
    if bucket is None:
        bucket = StorageBucket(
            tenant_id=tenant.id,
            provider=settings.storage_provider.value,
            bucket_name=bucket_name_value,
            region=region,
            prefix=settings.storage_bucket_prefix,
            is_default=True,
            status="ready",
        )
        session.add(bucket)

    results: dict[str, FixtureAssetResult] = {}
    for asset in assets:
        if asset.key in results:
            raise TestFixtureError(f"Duplicate asset fixture key '{asset.key}'.")

        conversation_id = resolve_conversation_id(asset.conversation_key, conversation_results)
        user_id = resolve_user_id(asset.user_email, user_results) if asset.user_email else None

        storage_object_id = uuid5(NAMESPACE_URL, f"fixture-storage:{tenant.id}:{asset.key}")
        asset_id = uuid5(NAMESPACE_URL, f"fixture-asset:{tenant.id}:{asset.key}")
        safe_name = safe_filename(asset.filename)
        object_key = f"{tenant.id}/{asset.key}/{safe_name}"
        mime_type = asset.mime_type or "application/octet-stream"
        size_bytes = asset.size_bytes if asset.size_bytes is not None else 0

        storage_obj = await session.scalar(
            select(StorageObject).where(StorageObject.id == storage_object_id)
        )
        if storage_obj is None:
            storage_obj = StorageObject(
                id=storage_object_id,
                tenant_id=tenant.id,
                bucket_id=bucket.id,
                object_key=object_key,
                filename=asset.filename,
                mime_type=mime_type,
                size_bytes=size_bytes,
                checksum_sha256=None,
                status="ready",
                created_by_user_id=user_id,
                agent_key=asset.agent_key,
                conversation_id=conversation_id,
                metadata_json=asset.metadata,
                expires_at=None,
            )
            session.add(storage_obj)
        else:
            storage_obj.bucket_id = bucket.id
            storage_obj.object_key = object_key
            storage_obj.filename = asset.filename
            storage_obj.mime_type = mime_type
            storage_obj.size_bytes = size_bytes
            storage_obj.status = storage_obj.status or "ready"
            storage_obj.created_by_user_id = user_id
            storage_obj.agent_key = asset.agent_key
            storage_obj.conversation_id = conversation_id
            storage_obj.metadata_json = asset.metadata
            storage_obj.deleted_at = None

        asset_row = await session.scalar(select(AgentAsset).where(AgentAsset.id == asset_id))
        if asset_row is None:
            asset_row = AgentAsset(
                id=asset_id,
                tenant_id=tenant.id,
                storage_object_id=storage_object_id,
                asset_type=asset.asset_type,
                source_tool=asset.source_tool,
                conversation_id=conversation_id,
                message_id=asset.message_id,
                tool_call_id=asset.tool_call_id,
                response_id=asset.response_id,
                container_id=asset.container_id,
                openai_file_id=asset.openai_file_id,
                metadata_json=asset.metadata,
            )
            session.add(asset_row)
        else:
            asset_row.storage_object_id = storage_object_id
            asset_row.asset_type = asset.asset_type
            asset_row.source_tool = asset.source_tool
            asset_row.conversation_id = conversation_id
            asset_row.message_id = asset.message_id
            asset_row.tool_call_id = asset.tool_call_id
            asset_row.response_id = asset.response_id
            asset_row.container_id = asset.container_id
            asset_row.openai_file_id = asset.openai_file_id
            asset_row.metadata_json = asset.metadata
            asset_row.deleted_at = None

        results[asset.key] = FixtureAssetResult(
            asset_id=str(asset_id),
            storage_object_id=str(storage_object_id),
        )

    return results


__all__ = ["ensure_assets"]
