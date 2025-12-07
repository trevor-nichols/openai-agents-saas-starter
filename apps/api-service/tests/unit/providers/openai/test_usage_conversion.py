from types import SimpleNamespace

from app.domain.ai import AgentRunUsage
from app.infrastructure.providers.openai.usage import convert_usage


def _usage(**kwargs):
    return SimpleNamespace(**kwargs)


def test_convert_usage_maps_extended_fields():
    usage = _usage(
        input_tokens=10,
        output_tokens=5,
        total_tokens=15,
        input_tokens_details=_usage(cached_tokens=7),
        output_tokens_details=_usage(reasoning_tokens=3),
        requests=2,
        request_usage_entries=[{"input_tokens": 5}],
    )

    result = convert_usage(usage)
    assert isinstance(result, AgentRunUsage)
    assert result.input_tokens == 10
    assert result.output_tokens == 5
    assert result.total_tokens == 15
    assert result.cached_input_tokens == 7
    assert result.reasoning_output_tokens == 3
    assert result.requests == 2
    assert result.request_usage_entries == [{"input_tokens": 5}]
