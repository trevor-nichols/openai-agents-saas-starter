"""Public endpoints exposing platform status snapshots."""

from __future__ import annotations

from email.utils import format_datetime
from uuid import UUID
from xml.etree import ElementTree as ET

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.api.dependencies.auth import CurrentUser, require_scopes
from app.api.v1.status.schemas import (
    PlatformStatusResponse,
    StatusIncidentResendRequest,
    StatusIncidentResendResponse,
    StatusSubscriptionChallengeRequest,
    StatusSubscriptionCreateRequest,
    StatusSubscriptionListResponse,
    StatusSubscriptionResponse,
    StatusSubscriptionVerifyRequest,
)
from app.bootstrap import get_container
from app.core.security import get_current_user
from app.core.settings import get_settings
from app.domain.status import PlatformStatusSnapshot
from app.services.status.status_alert_dispatcher import StatusAlertDispatcher
from app.services.status.status_service import get_status_service
from app.services.status.status_subscription_service import StatusSubscriptionService

router = APIRouter(prefix="/status", tags=["status"])
_settings = get_settings()
_status_service = get_status_service()
_optional_bearer = HTTPBearer(auto_error=False)


async def _get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_optional_bearer),
) -> CurrentUser | None:
    if credentials is None:
        return None
    return await get_current_user(credentials)


def _get_subscription_service() -> StatusSubscriptionService:
    container = get_container()
    service = container.status_subscription_service
    if service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Status subscriptions are unavailable.",
        )
    return service


def _get_alert_dispatcher() -> StatusAlertDispatcher:
    container = get_container()
    dispatcher = container.status_alert_dispatcher
    if dispatcher is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Status alert dispatcher unavailable.",
        )
    return dispatcher


def _resolve_tenant_id(user: CurrentUser | None) -> UUID | None:
    if not user:
        return None
    payload = user.get("payload") or {}
    raw = payload.get("tenant_id")
    if isinstance(raw, str):
        try:
            return UUID(raw)
        except ValueError:
            return None
    return None


def _client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        candidate = forwarded.split(",")[0].strip()
        if candidate:
            return candidate
    forwarded_header = request.headers.get("forwarded")
    if forwarded_header:
        for part in forwarded_header.split(","):
            for segment in part.split(";"):
                segment = segment.strip()
                if segment.lower().startswith("for="):
                    value = segment[4:].strip().strip('"')
                    if value:
                        return value
    if request.client:
        return request.client.host
    return None


def _validate_cursor(cursor: str | None) -> str | None:
    if cursor is None:
        return None
    try:
        value = int(cursor)
        if value < 0:
            raise ValueError
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid cursor.",
        ) from None
    return cursor


@router.get("", response_model=PlatformStatusResponse)
async def get_platform_status() -> PlatformStatusResponse:
    """Return the latest platform status snapshot."""

    snapshot = await _status_service.get_platform_status()
    return PlatformStatusResponse.from_snapshot(snapshot)


@router.get("/rss", response_class=Response)
async def get_platform_status_rss() -> Response:
    """Return the incident feed as an RSS document."""

    return await _build_status_rss_response()


@router.get(".rss", response_class=Response, include_in_schema=False)
async def get_platform_status_rss_dot() -> Response:
    """Alias for the RSS feed endpoint (for clients expecting `/status.rss`)."""

    return await _build_status_rss_response()


async def _build_status_rss_response() -> Response:
    snapshot = await _status_service.get_platform_status()
    rss_xml = _render_snapshot_as_rss(
        snapshot,
        status_url=f"{_settings.app_public_url.rstrip('/')}/status",
    )
    return Response(content=rss_xml, media_type="application/rss+xml; charset=utf-8")


def _render_snapshot_as_rss(snapshot: PlatformStatusSnapshot, *, status_url: str) -> str:
    feed = ET.Element("rss", version="2.0")
    channel = ET.SubElement(feed, "channel")
    ET.SubElement(channel, "title").text = "Acme Platform Status"
    ET.SubElement(channel, "link").text = status_url
    ET.SubElement(channel, "description").text = snapshot.overview.description
    ET.SubElement(channel, "lastBuildDate").text = format_datetime(snapshot.generated_at)
    ET.SubElement(channel, "pubDate").text = format_datetime(snapshot.generated_at)

    for incident in snapshot.incidents:
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = f"{incident.service}: {incident.impact}"
        ET.SubElement(item, "link").text = status_url
        ET.SubElement(item, "guid").text = incident.incident_id
        ET.SubElement(item, "pubDate").text = format_datetime(incident.occurred_at)
        ET.SubElement(item, "description").text = incident.impact

    return ET.tostring(feed, encoding="utf-8", xml_declaration=True).decode("utf-8")


@router.post(
    "/subscriptions",
    response_model=StatusSubscriptionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_status_subscription(
    payload: StatusSubscriptionCreateRequest,
    request: Request,
    user: CurrentUser | None = Depends(_get_optional_user),
):
    service = _get_subscription_service()
    tenant_id = _resolve_tenant_id(user)
    creator_value = user.get("user_id") if user else None
    created_by = str(creator_value) if creator_value else "public"
    if payload.channel == "webhook":
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required for webhook subscriptions.",
            )
        user = require_scopes("status:manage")(user=user)
    result = await service.create_subscription(
        channel=payload.channel,
        target=payload.target,
        severity_filter=payload.severity_filter or "major",
        metadata=payload.metadata or {},
        tenant_id=tenant_id,
        created_by=created_by,
        ip_address=_client_ip(request),
    )
    response = StatusSubscriptionResponse.from_domain(result.subscription)
    if result.webhook_secret:
        response.webhook_secret = result.webhook_secret
    return response


@router.post("/subscriptions/verify", response_model=StatusSubscriptionResponse)
async def verify_status_subscription(payload: StatusSubscriptionVerifyRequest):
    service = _get_subscription_service()
    record = await service.verify_email_token(token=payload.token)
    return StatusSubscriptionResponse.from_domain(record)


@router.post("/subscriptions/challenge", response_model=StatusSubscriptionResponse)
async def confirm_webhook_challenge(payload: StatusSubscriptionChallengeRequest):
    service = _get_subscription_service()
    record = await service.confirm_webhook_challenge(token=payload.token)
    return StatusSubscriptionResponse.from_domain(record)


@router.get("/subscriptions", response_model=StatusSubscriptionListResponse)
async def list_status_subscriptions(
    limit: int = 20,
    cursor: str | None = None,
    tenant_id: UUID | None = Query(
        default=None,
        description="Tenant identifier to inspect (operators only).",
    ),
    all_tenants: bool = Query(
        default=False,
        alias="all",
        description=(
            "When true, ignore token tenant scoping and return subscriptions across all tenants."
        ),
    ),
    user: CurrentUser = Depends(require_scopes("status:manage")),
):
    service = _get_subscription_service()
    session_tenant = _resolve_tenant_id(user)
    tenant_scope: UUID | None

    if session_tenant and not all_tenants:
        if tenant_id and tenant_id != session_tenant:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tenant-scoped tokens cannot override tenant_id without all=true.",
            )
        tenant_scope = session_tenant
    else:
        tenant_scope = (
            tenant_id
            if tenant_id is not None
            else (None if all_tenants else session_tenant)
        )

    safe_cursor = _validate_cursor(cursor)
    result = await service.list_subscriptions(
        tenant_id=tenant_scope,
        status_filter=None,
        limit=limit,
        cursor=safe_cursor,
    )
    return StatusSubscriptionListResponse.from_result(result)


@router.delete("/subscriptions/{subscription_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_status_subscription(
    subscription_id: UUID,
    token: str | None = Query(
        default=None,
        description="Unsubscribe token for email subscribers.",
    ),
    user: CurrentUser | None = Depends(_get_optional_user),
):
    service = _get_subscription_service()
    if token:
        record = await service.get_subscription_by_unsubscribe_token(token=token)
        if record.id != subscription_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token does not match subscription.",
            )
        await service.revoke_subscription(subscription_id, reason="user_unsubscribe")
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
        )
    require_scopes("status:manage")(user=user)
    await service.revoke_subscription(
        subscription_id,
        reason=f"revoked-by:{user.get('user_id', 'system')}",
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/incidents/{incident_id}/resend",
    response_model=StatusIncidentResendResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def resend_status_incident(
    incident_id: str,
    payload: StatusIncidentResendRequest,
    user: CurrentUser = Depends(require_scopes("status:manage")),
):
    dispatcher = _get_alert_dispatcher()
    snapshot = await _status_service.get_platform_status()
    incident = next((item for item in snapshot.incidents if item.incident_id == incident_id), None)
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found.")
    tenant_scope = _resolve_tenant_id(user) or payload.tenant_id
    dispatched = await dispatcher.dispatch_incident(
        incident,
        severity=payload.severity,
        tenant_id=tenant_scope,
    )
    return StatusIncidentResendResponse(dispatched=dispatched)
