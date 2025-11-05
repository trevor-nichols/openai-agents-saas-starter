Usage
Usage
Source code in src/agents/usage.py
requests class-attribute instance-attribute

requests: int = 0
Total requests made to the LLM API.

input_tokens class-attribute instance-attribute

input_tokens: int = 0
Total input tokens sent, across all requests.

input_tokens_details class-attribute instance-attribute

input_tokens_details: InputTokensDetails = field(
    default_factory=lambda: InputTokensDetails(
        cached_tokens=0
    )
)
Details about the input tokens, matching responses API usage details.

output_tokens class-attribute instance-attribute

output_tokens: int = 0
Total output tokens received, across all requests.

output_tokens_details class-attribute instance-attribute

output_tokens_details: OutputTokensDetails = field(
    default_factory=lambda: OutputTokensDetails(
        reasoning_tokens=0
    )
)
Details about the output tokens, matching responses API usage details.

total_tokens class-attribute instance-attribute

total_tokens: int = 0
Total tokens sent and received, across all requests.

