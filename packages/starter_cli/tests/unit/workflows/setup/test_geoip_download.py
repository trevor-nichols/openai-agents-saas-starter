from __future__ import annotations

import io
import tarfile
from pathlib import Path

import httpx
import pytest
from starter_cli.core import CLIError
from starter_cli.workflows.setup.geoip import download_maxmind_database
from starter_cli.ports.console import StdConsole


def _build_tarball() -> bytes:
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
        payload = b"geoip"
        info = tarfile.TarInfo(name="GeoLite2-City.mmdb")
        info.size = len(payload)
        archive.addfile(info, io.BytesIO(payload))
    return buffer.getvalue()


@pytest.mark.parametrize("status", [200, 401])
def test_download_maxmind_database(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, status: int
) -> None:
    responses = {
        200: httpx.Response(200, content=_build_tarball()),
        401: httpx.Response(401, text="unauthorized"),
    }

    class DummyClient:
        def __init__(self, timeout: float) -> None:
            self.timeout = timeout
            self.closed = False

        def get(self, url: str) -> httpx.Response:
            self.url = url
            return responses[status]

        def close(self) -> None:
            self.closed = True

    monkeypatch.setattr(httpx, "Client", DummyClient)
    target = tmp_path / "GeoLite2-City.mmdb"
    if status == 200:
        download_maxmind_database(license_key="abc", target_path=target, console=StdConsole())
        assert target.exists()
        assert target.read_bytes() == b"geoip"
    else:
        with pytest.raises(CLIError):
            download_maxmind_database(license_key="abc", target_path=target, console=StdConsole())
