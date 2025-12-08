"""Individual guardrail check implementations.

Each subdirectory contains:
- spec.py: GuardrailSpec definition via get_guardrail_spec()
- check.py: The async check function (run_check)

Available guardrails:
- pii_detection_input: Detects PII on inputs/pre-flight (mask/block)
- pii_detection_output: Detects PII on outputs (mask/block)
- jailbreak_detection: Detects jailbreak/bypass attempts
- prompt_injection: Detects prompt injection in tool calls
- hallucination: Detects unsupported factual claims
- moderation: OpenAI content moderation
- url_filter: URL allow/block list filtering
- custom_prompt: Custom LLM-based checks
"""

# Check modules are loaded dynamically by the loader
__all__: list[str] = []
