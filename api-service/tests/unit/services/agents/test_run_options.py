from app.services.agents.run_options import build_run_options
from app.domain.ai import RunOptions


class DummyPayload:
    def __init__(self, max_turns=None, previous_response_id=None, handoff_input_filter=None, run_config=None):
        self.max_turns = max_turns
        self.previous_response_id = previous_response_id
        self.handoff_input_filter = handoff_input_filter
        self.run_config = run_config


def test_build_run_options_none_payload():
    opts = build_run_options(None)
    assert opts is None


def test_build_run_options_simple_payload():
    payload = DummyPayload(max_turns=3, previous_response_id="resp-1", handoff_input_filter="all", run_config={"temperature":0.2})
    opts = build_run_options(payload)
    assert isinstance(opts, RunOptions)
    assert opts.max_turns == 3
    assert opts.previous_response_id == "resp-1"
    assert opts.handoff_input_filter == "all"
    assert opts.run_config == {"temperature": 0.2}
    assert opts.hook_sink is None


def test_build_run_options_with_hook_sink():
    payload = DummyPayload()
    sentinel = object()
    opts = build_run_options(payload, hook_sink=sentinel)
    assert opts.hook_sink is sentinel


def test_build_run_options_plain_dict_missing_attrs():
    payload = {"unrelated": 1}
    opts = build_run_options(payload)
    assert isinstance(opts, RunOptions)
    assert opts.max_turns is None
    assert opts.previous_response_id is None
    assert opts.handoff_input_filter is None
    assert opts.run_config is None
