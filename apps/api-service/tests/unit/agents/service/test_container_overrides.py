from __future__ import annotations

from dataclasses import dataclass
from typing import cast
from uuid import uuid4

import pytest

from app.agents._shared.specs import AgentSpec
from app.services.agents.container_overrides import (
    ContainerOverrideError,
    ContainerOverrideResolver,
)
from app.services.containers import ContainerNotFoundError, ContainerService


@dataclass(slots=True)
class _FakeContainer:
    id: str
    openai_id: str
    tenant_id: str


class _FakeContainerService:
    def __init__(self, containers: list[_FakeContainer]):
        self._containers = containers

    async def get_container(self, *, container_id, tenant_id):
        for container in self._containers:
            if str(container.id) == str(container_id) and container.tenant_id == str(tenant_id):
                return container
        raise ContainerNotFoundError("not found")


def _resolver(*, spec: AgentSpec, containers: list[_FakeContainer]):
    resolver = ContainerOverrideResolver(
        container_service=cast(ContainerService, _FakeContainerService(containers))
    )
    resolver._spec_index = {spec.key: spec}
    return resolver


@pytest.mark.asyncio
async def test_resolves_valid_container_override():
    tenant_id = str(uuid4())
    container_id = str(uuid4())
    container = _FakeContainer(id=container_id, openai_id="openai-1", tenant_id=tenant_id)
    spec = AgentSpec(
        key="ci_agent",
        display_name="CI",
        description="",
        instructions="",
        tool_keys=("code_interpreter",),
    )
    resolver = _resolver(spec=spec, containers=[container])

    resolved = await resolver.resolve(
        overrides={"ci_agent": container_id},
        tenant_id=tenant_id,
        allowed_agent_keys=["ci_agent"],
    )

    assert resolved is not None
    assert resolved["ci_agent"].openai_container_id == "openai-1"
    assert resolved["ci_agent"].container_id == container_id


@pytest.mark.asyncio
async def test_rejects_agent_without_code_interpreter():
    tenant_id = str(uuid4())
    container_id = str(uuid4())
    container = _FakeContainer(id=container_id, openai_id="openai-1", tenant_id=tenant_id)
    spec = AgentSpec(
        key="no_ci",
        display_name="No CI",
        description="",
        instructions="",
        tool_keys=(),
    )
    resolver = _resolver(spec=spec, containers=[container])

    with pytest.raises(ContainerOverrideError):
        await resolver.resolve(
            overrides={"no_ci": container_id},
            tenant_id=tenant_id,
            allowed_agent_keys=["no_ci"],
        )


@pytest.mark.asyncio
async def test_rejects_invalid_container_id():
    tenant_id = str(uuid4())
    spec = AgentSpec(
        key="ci_agent",
        display_name="CI",
        description="",
        instructions="",
        tool_keys=("code_interpreter",),
    )
    resolver = _resolver(spec=spec, containers=[])

    with pytest.raises(ContainerOverrideError):
        await resolver.resolve(
            overrides={"ci_agent": "not-a-uuid"},
            tenant_id=tenant_id,
            allowed_agent_keys=["ci_agent"],
        )


@pytest.mark.asyncio
async def test_rejects_container_not_found():
    tenant_id = str(uuid4())
    container_id = str(uuid4())
    spec = AgentSpec(
        key="ci_agent",
        display_name="CI",
        description="",
        instructions="",
        tool_keys=("code_interpreter",),
    )
    resolver = _resolver(spec=spec, containers=[])

    with pytest.raises(ContainerOverrideError):
        await resolver.resolve(
            overrides={"ci_agent": container_id},
            tenant_id=tenant_id,
            allowed_agent_keys=["ci_agent"],
        )


@pytest.mark.asyncio
async def test_rejects_override_for_out_of_scope_agent():
    tenant_id = str(uuid4())
    container_id = str(uuid4())
    container = _FakeContainer(id=container_id, openai_id="openai-1", tenant_id=tenant_id)
    spec = AgentSpec(
        key="ci_agent",
        display_name="CI",
        description="",
        instructions="",
        tool_keys=("code_interpreter",),
    )
    resolver = _resolver(spec=spec, containers=[container])

    with pytest.raises(ContainerOverrideError):
        await resolver.resolve(
            overrides={"ci_agent": container_id},
            tenant_id=tenant_id,
            allowed_agent_keys=["other_agent"],
        )
