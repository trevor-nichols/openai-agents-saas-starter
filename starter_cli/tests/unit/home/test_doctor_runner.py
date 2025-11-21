from __future__ import annotations

import json
from pathlib import Path

import jsonschema
from starter_cli.core.context import build_context
from starter_cli.core.status_models import ProbeResult, ProbeState
from starter_cli.workflows.home.doctor import DoctorRunner


def _stub_probes_ok_warn():
    return [
        ProbeResult(name="env", state=ProbeState.OK, detail="ok"),
        ProbeResult(name="stripe", state=ProbeState.WARN, detail="missing"),
    ]


def _empty_services(_probes):
    return []


def test_doctor_exit_code_respects_strict(monkeypatch, tmp_path: Path):
    ctx = build_context()
    runner = DoctorRunner(ctx, profile="local", strict=False)
    monkeypatch.setattr(runner, "_run_probes", _stub_probes_ok_warn)
    monkeypatch.setattr(runner, "_build_services", _empty_services)

    code = runner.run(json_path=tmp_path / "report.json")
    assert code == 0  # warn allowed when not strict/local

    data = json.loads((tmp_path / "report.json").read_text())
    assert data["summary"]["warn"] == 1

    runner_strict = DoctorRunner(ctx, profile="local", strict=True)
    monkeypatch.setattr(runner_strict, "_run_probes", _stub_probes_ok_warn)
    monkeypatch.setattr(runner_strict, "_build_services", _empty_services)
    code = runner_strict.run()
    assert code == 1  # warn promoted to error under strict


def test_doctor_markdown_writes_file(monkeypatch, tmp_path: Path):
    ctx = build_context()
    runner = DoctorRunner(ctx, profile="local", strict=False)
    monkeypatch.setattr(runner, "_run_probes", _stub_probes_ok_warn)
    monkeypatch.setattr(runner, "_build_services", _empty_services)
    md_path = tmp_path / "report.md"
    runner.run(markdown_path=md_path)
    assert md_path.exists()
    content = md_path.read_text()
    assert "Doctor Report" in content
    assert "stripe" in content


def test_doctor_json_matches_schema(monkeypatch, tmp_path: Path):
    ctx = build_context()
    runner = DoctorRunner(ctx, profile="local", strict=False)
    monkeypatch.setattr(runner, "_run_probes", _stub_probes_ok_warn)
    monkeypatch.setattr(runner, "_build_services", _empty_services)
    json_path = tmp_path / "report.json"
    md_path = tmp_path / "report.md"
    code = runner.run(json_path=json_path, markdown_path=md_path)
    assert code == 0
    from starter_cli.core.constants import PROJECT_ROOT

    schema_path = PROJECT_ROOT / "starter_contracts" / "doctor_v1.json"
    schema = json.loads(schema_path.read_text())
    payload = json.loads(json_path.read_text())
    jsonschema.validate(instance=payload, schema=schema)
    assert payload["summary"]["warn"] == 1
    assert md_path.exists()
