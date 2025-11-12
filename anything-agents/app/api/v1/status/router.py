"""Public endpoints exposing platform status snapshots."""

from __future__ import annotations

from email.utils import format_datetime
from xml.etree import ElementTree as ET

from fastapi import APIRouter, Response

from app.api.v1.status.schemas import PlatformStatusResponse
from app.core.config import get_settings
from app.domain.status import PlatformStatusSnapshot
from app.services.status_service import get_status_service

router = APIRouter(prefix="/status", tags=["status"])
_settings = get_settings()
_status_service = get_status_service()


@router.get("", response_model=PlatformStatusResponse)
async def get_platform_status() -> PlatformStatusResponse:
    """Return the latest platform status snapshot."""

    snapshot = await _status_service.get_platform_status()
    return PlatformStatusResponse.from_snapshot(snapshot)


@router.get("/rss", response_class=Response)
async def get_platform_status_rss() -> Response:
    """Return the incident feed as an RSS document."""

    snapshot = await _status_service.get_platform_status()
    rss_xml = _render_snapshot_as_rss(
        snapshot,
        status_url=f"{_settings.app_public_url.rstrip('/')}/status",
    )
    return Response(content=rss_xml, media_type="application/rss+xml; charset=utf-8")


def _render_snapshot_as_rss(snapshot: PlatformStatusSnapshot, *, status_url: str) -> str:
    feed = ET.Element("rss", version="2.0")
    channel = ET.SubElement(feed, "channel")
    ET.SubElement(channel, "title").text = "Anything Agents Platform Status"
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
