from __future__ import annotations

import io
import tarfile
from pathlib import Path
from typing import Final

import httpx

from starter_console.core import CLIError
from starter_console.ports.console import ConsolePort

MAXMIND_DEFAULT_EDITION: Final[str] = "GeoLite2-City"


def download_maxmind_database(
    *,
    license_key: str,
    target_path: Path,
    edition_id: str = MAXMIND_DEFAULT_EDITION,
    console: ConsolePort,
) -> Path:
    if not license_key:
        raise CLIError("MaxMind license key is required before downloading the database.")
    url = (
        "https://download.maxmind.com/app/geoip_download"
        f"?edition_id={edition_id}&license_key={license_key}&suffix=tar.gz"
    )
    console.info(f"Downloading {edition_id} from MaxMind …", topic="geoip")
    client = httpx.Client(timeout=60.0)
    try:
        response = client.get(url)
    finally:
        client.close()
    if response.status_code >= 400:
        raise CLIError(
            f"MaxMind download failed ({response.status_code}). "
            "Verify the license key and account permissions."
        )
    data = response.content
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as archive:
        member = next((m for m in archive.getmembers() if m.name.endswith(".mmdb")), None)
        if member is None:
            raise CLIError("MaxMind archive did not include an .mmdb file.")
        file_handle = archive.extractfile(member)
        if file_handle is None:
            raise CLIError("MaxMind archive is corrupted; unable to read .mmdb payload.")
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with target_path.open("wb") as destination:
            destination.write(file_handle.read())
    console.success(f"Saved GeoIP database to {target_path}", topic="geoip")
    return target_path


__all__ = ["download_maxmind_database", "MAXMIND_DEFAULT_EDITION"]
