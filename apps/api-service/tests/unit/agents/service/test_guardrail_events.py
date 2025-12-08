from __future__ import annotations

from app.api.v1.shared.stream_normalizer import normalize_stream_event
from app.api.v1.shared.streaming import StreamingEvent
from app.domain.ai.models import AgentStreamEvent
from app.services.agent_service import AgentService


def test_normalize_guardrail_event():
    event = AgentStreamEvent(
        kind="guardrail_result",
        conversation_id="conv1",
        agent="triage",
        guardrail_stage="input",
        guardrail_key="pii_detection_input",
        guardrail_name="PII Detection (Input)",
        guardrail_tripwire_triggered=True,
        guardrail_suppressed=False,
        guardrail_flagged=True,
        guardrail_confidence=0.9,
        guardrail_masked_content="[redacted]",
        guardrail_token_usage={"total_tokens": 12},
        guardrail_details={"flagged": True},
    )

    normalized: StreamingEvent = normalize_stream_event(event)

    assert normalized.kind == "guardrail_result"
    assert normalized.guardrail_stage == "input"
    assert normalized.guardrail_key == "pii_detection_input"
    assert normalized.guardrail_tripwire_triggered is True
    assert normalized.guardrail_suppressed is False
    assert normalized.guardrail_flagged is True
    assert normalized.guardrail_confidence == 0.9
    assert normalized.guardrail_masked_content == "[redacted]"
    assert normalized.guardrail_token_usage == {"total_tokens": 12}
    assert normalized.guardrail_details == {"flagged": True}


def test_guardrail_summary_builder():
    events = [
        {
            "guardrail_stage": "input",
            "guardrail_key": "pii_detection_input",
            "guardrail_tripwire_triggered": True,
            "guardrail_suppressed": False,
            "guardrail_token_usage": {"total_tokens": 5, "prompt_tokens": 2},
        },
        {
            "guardrail_stage": "output",
            "guardrail_key": "nsfw_text",
            "guardrail_tripwire_triggered": False,
            "guardrail_suppressed": False,
            "guardrail_token_usage": {"total_tokens": 7, "completion_tokens": 3},
        },
        {
            "guardrail_stage": "input",
            "guardrail_key": "off_topic_prompts",
            "guardrail_tripwire_triggered": True,
            "guardrail_suppressed": True,
        },
    ]

    summary = AgentService._build_guardrail_summary(events)

    assert summary["total"] == 3
    assert summary["triggered"] == 2
    assert summary["suppressed"] == 1
    assert summary["by_stage"]["input"]["total"] == 2
    assert summary["by_stage"]["input"]["triggered"] == 2
    assert summary["by_stage"]["output"]["total"] == 1
    assert summary["by_key"]["pii_detection_input"] == 1
    assert summary["by_key"]["nsfw_text"] == 1
    assert summary["by_key"]["off_topic_prompts"] == 1
    assert summary["token_usage"]["total_tokens"] == 12
    assert summary["token_usage"]["prompt_tokens"] == 2
    assert summary["token_usage"]["completion_tokens"] == 3
