Creating traces/spans
trace

trace(
    workflow_name: str,
    trace_id: str | None = None,
    group_id: str | None = None,
    metadata: dict[str, Any] | None = None,
    disabled: bool = False,
) -> Trace
Create a new trace. The trace will not be started automatically; you should either use it as a context manager (with trace(...):) or call trace.start() + trace.finish() manually.

In addition to the workflow name and optional grouping identifier, you can provide an arbitrary metadata dictionary to attach additional user-defined information to the trace.

Parameters:

Name	Type	Description	Default
workflow_name	str	The name of the logical app or workflow. For example, you might provide "code_bot" for a coding agent, or "customer_support_agent" for a customer support agent.	required
trace_id	str | None	The ID of the trace. Optional. If not provided, we will generate an ID. We recommend using util.gen_trace_id() to generate a trace ID, to guarantee that IDs are correctly formatted.	None
group_id	str | None	Optional grouping identifier to link multiple traces from the same conversation or process. For instance, you might use a chat thread ID.	None
metadata	dict[str, Any] | None	Optional dictionary of additional metadata to attach to the trace.	None
disabled	bool	If True, we will return a Trace but the Trace will not be recorded.	False
Returns:

Type	Description
Trace	The newly created trace object.
Source code in src/agents/tracing/create.py
get_current_trace

get_current_trace() -> Trace | None
Returns the currently active trace, if present.

Source code in src/agents/tracing/create.py
get_current_span

get_current_span() -> Span[Any] | None
Returns the currently active span, if present.

Source code in src/agents/tracing/create.py
agent_span

agent_span(
    name: str,
    handoffs: list[str] | None = None,
    tools: list[str] | None = None,
    output_type: str | None = None,
    span_id: str | None = None,
    parent: Trace | Span[Any] | None = None,
    disabled: bool = False,
) -> Span[AgentSpanData]
Create a new agent span. The span will not be started automatically, you should either do with agent_span() ... or call span.start() + span.finish() manually.

Parameters:

Name	Type	Description	Default
name	str	The name of the agent.	required
handoffs	list[str] | None	Optional list of agent names to which this agent could hand off control.	None
tools	list[str] | None	Optional list of tool names available to this agent.	None
output_type	str | None	Optional name of the output type produced by the agent.	None
span_id	str | None	The ID of the span. Optional. If not provided, we will generate an ID. We recommend using util.gen_span_id() to generate a span ID, to guarantee that IDs are correctly formatted.	None
parent	Trace | Span[Any] | None	The parent span or trace. If not provided, we will automatically use the current trace/span as the parent.	None
disabled	bool	If True, we will return a Span but the Span will not be recorded.	False
Returns:

Type	Description
Span[AgentSpanData]	The newly created agent span.
Source code in src/agents/tracing/create.py
function_span

function_span(
    name: str,
    input: str | None = None,
    output: str | None = None,
    span_id: str | None = None,
    parent: Trace | Span[Any] | None = None,
    disabled: bool = False,
) -> Span[FunctionSpanData]
Create a new function span. The span will not be started automatically, you should either do with function_span() ... or call span.start() + span.finish() manually.

Parameters:

Name	Type	Description	Default
name	str	The name of the function.	required
input	str | None	The input to the function.	None
output	str | None	The output of the function.	None
span_id	str | None	The ID of the span. Optional. If not provided, we will generate an ID. We recommend using util.gen_span_id() to generate a span ID, to guarantee that IDs are correctly formatted.	None
parent	Trace | Span[Any] | None	The parent span or trace. If not provided, we will automatically use the current trace/span as the parent.	None
disabled	bool	If True, we will return a Span but the Span will not be recorded.	False
Returns:

Type	Description
Span[FunctionSpanData]	The newly created function span.
Source code in src/agents/tracing/create.py
generation_span

generation_span(
    input: Sequence[Mapping[str, Any]] | None = None,
    output: Sequence[Mapping[str, Any]] | None = None,
    model: str | None = None,
    model_config: Mapping[str, Any] | None = None,
    usage: dict[str, Any] | None = None,
    span_id: str | None = None,
    parent: Trace | Span[Any] | None = None,
    disabled: bool = False,
) -> Span[GenerationSpanData]
Create a new generation span. The span will not be started automatically, you should either do with generation_span() ... or call span.start() + span.finish() manually.

This span captures the details of a model generation, including the input message sequence, any generated outputs, the model name and configuration, and usage data. If you only need to capture a model response identifier, use response_span() instead.

Parameters:

Name	Type	Description	Default
input	Sequence[Mapping[str, Any]] | None	The sequence of input messages sent to the model.	None
output	Sequence[Mapping[str, Any]] | None	The sequence of output messages received from the model.	None
model	str | None	The model identifier used for the generation.	None
model_config	Mapping[str, Any] | None	The model configuration (hyperparameters) used.	None
usage	dict[str, Any] | None	A dictionary of usage information (input tokens, output tokens, etc.).	None
span_id	str | None	The ID of the span. Optional. If not provided, we will generate an ID. We recommend using util.gen_span_id() to generate a span ID, to guarantee that IDs are correctly formatted.	None
parent	Trace | Span[Any] | None	The parent span or trace. If not provided, we will automatically use the current trace/span as the parent.	None
disabled	bool	If True, we will return a Span but the Span will not be recorded.	False
Returns:

Type	Description
Span[GenerationSpanData]	The newly created generation span.
Source code in src/agents/tracing/create.py
response_span

response_span(
    response: Response | None = None,
    span_id: str | None = None,
    parent: Trace | Span[Any] | None = None,
    disabled: bool = False,
) -> Span[ResponseSpanData]
Create a new response span. The span will not be started automatically, you should either do with response_span() ... or call span.start() + span.finish() manually.

Parameters:

Name	Type	Description	Default
response	Response | None	The OpenAI Response object.	None
span_id	str | None	The ID of the span. Optional. If not provided, we will generate an ID. We recommend using util.gen_span_id() to generate a span ID, to guarantee that IDs are correctly formatted.	None
parent	Trace | Span[Any] | None	The parent span or trace. If not provided, we will automatically use the current trace/span as the parent.	None
disabled	bool	If True, we will return a Span but the Span will not be recorded.	False
Source code in src/agents/tracing/create.py
handoff_span

handoff_span(
    from_agent: str | None = None,
    to_agent: str | None = None,
    span_id: str | None = None,
    parent: Trace | Span[Any] | None = None,
    disabled: bool = False,
) -> Span[HandoffSpanData]
Create a new handoff span. The span will not be started automatically, you should either do with handoff_span() ... or call span.start() + span.finish() manually.

Parameters:

Name	Type	Description	Default
from_agent	str | None	The name of the agent that is handing off.	None
to_agent	str | None	The name of the agent that is receiving the handoff.	None
span_id	str | None	The ID of the span. Optional. If not provided, we will generate an ID. We recommend using util.gen_span_id() to generate a span ID, to guarantee that IDs are correctly formatted.	None
parent	Trace | Span[Any] | None	The parent span or trace. If not provided, we will automatically use the current trace/span as the parent.	None
disabled	bool	If True, we will return a Span but the Span will not be recorded.	False
Returns:

Type	Description
Span[HandoffSpanData]	The newly created handoff span.
Source code in src/agents/tracing/create.py
custom_span

custom_span(
    name: str,
    data: dict[str, Any] | None = None,
    span_id: str | None = None,
    parent: Trace | Span[Any] | None = None,
    disabled: bool = False,
) -> Span[CustomSpanData]
Create a new custom span, to which you can add your own metadata. The span will not be started automatically, you should either do with custom_span() ... or call span.start() + span.finish() manually.

Parameters:

Name	Type	Description	Default
name	str	The name of the custom span.	required
data	dict[str, Any] | None	Arbitrary structured data to associate with the span.	None
span_id	str | None	The ID of the span. Optional. If not provided, we will generate an ID. We recommend using util.gen_span_id() to generate a span ID, to guarantee that IDs are correctly formatted.	None
parent	Trace | Span[Any] | None	The parent span or trace. If not provided, we will automatically use the current trace/span as the parent.	None
disabled	bool	If True, we will return a Span but the Span will not be recorded.	False
Returns:

Type	Description
Span[CustomSpanData]	The newly created custom span.
Source code in src/agents/tracing/create.py
guardrail_span

guardrail_span(
    name: str,
    triggered: bool = False,
    span_id: str | None = None,
    parent: Trace | Span[Any] | None = None,
    disabled: bool = False,
) -> Span[GuardrailSpanData]
Create a new guardrail span. The span will not be started automatically, you should either do with guardrail_span() ... or call span.start() + span.finish() manually.

Parameters:

Name	Type	Description	Default
name	str	The name of the guardrail.	required
triggered	bool	Whether the guardrail was triggered.	False
span_id	str | None	The ID of the span. Optional. If not provided, we will generate an ID. We recommend using util.gen_span_id() to generate a span ID, to guarantee that IDs are correctly formatted.	None
parent	Trace | Span[Any] | None	The parent span or trace. If not provided, we will automatically use the current trace/span as the parent.	None
disabled	bool	If True, we will return a Span but the Span will not be recorded.	False
Source code in src/agents/tracing/create.py
transcription_span

transcription_span(
    model: str | None = None,
    input: str | None = None,
    input_format: str | None = "pcm",
    output: str | None = None,
    model_config: Mapping[str, Any] | None = None,
    span_id: str | None = None,
    parent: Trace | Span[Any] | None = None,
    disabled: bool = False,
) -> Span[TranscriptionSpanData]
Create a new transcription span. The span will not be started automatically, you should either do with transcription_span() ... or call span.start() + span.finish() manually.

Parameters:

Name	Type	Description	Default
model	str | None	The name of the model used for the speech-to-text.	None
input	str | None	The audio input of the speech-to-text transcription, as a base64 encoded string of audio bytes.	None
input_format	str | None	The format of the audio input (defaults to "pcm").	'pcm'
output	str | None	The output of the speech-to-text transcription.	None
model_config	Mapping[str, Any] | None	The model configuration (hyperparameters) used.	None
span_id	str | None	The ID of the span. Optional. If not provided, we will generate an ID. We recommend using util.gen_span_id() to generate a span ID, to guarantee that IDs are correctly formatted.	None
parent	Trace | Span[Any] | None	The parent span or trace. If not provided, we will automatically use the current trace/span as the parent.	None
disabled	bool	If True, we will return a Span but the Span will not be recorded.	False
Returns:

Type	Description
Span[TranscriptionSpanData]	The newly created speech-to-text span.
Source code in src/agents/tracing/create.py
speech_span

speech_span(
    model: str | None = None,
    input: str | None = None,
    output: str | None = None,
    output_format: str | None = "pcm",
    model_config: Mapping[str, Any] | None = None,
    first_content_at: str | None = None,
    span_id: str | None = None,
    parent: Trace | Span[Any] | None = None,
    disabled: bool = False,
) -> Span[SpeechSpanData]
Create a new speech span. The span will not be started automatically, you should either do with speech_span() ... or call span.start() + span.finish() manually.

Parameters:

Name	Type	Description	Default
model	str | None	The name of the model used for the text-to-speech.	None
input	str | None	The text input of the text-to-speech.	None
output	str | None	The audio output of the text-to-speech as base64 encoded string of PCM audio bytes.	None
output_format	str | None	The format of the audio output (defaults to "pcm").	'pcm'
model_config	Mapping[str, Any] | None	The model configuration (hyperparameters) used.	None
first_content_at	str | None	The time of the first byte of the audio output.	None
span_id	str | None	The ID of the span. Optional. If not provided, we will generate an ID. We recommend using util.gen_span_id() to generate a span ID, to guarantee that IDs are correctly formatted.	None
parent	Trace | Span[Any] | None	The parent span or trace. If not provided, we will automatically use the current trace/span as the parent.	None
disabled	bool	If True, we will return a Span but the Span will not be recorded.	False
Source code in src/agents/tracing/create.py
speech_group_span

speech_group_span(
    input: str | None = None,
    span_id: str | None = None,
    parent: Trace | Span[Any] | None = None,
    disabled: bool = False,
) -> Span[SpeechGroupSpanData]
Create a new speech group span. The span will not be started automatically, you should either do with speech_group_span() ... or call span.start() + span.finish() manually.

Parameters:

Name	Type	Description	Default
input	str | None	The input text used for the speech request.	None
span_id	str | None	The ID of the span. Optional. If not provided, we will generate an ID. We recommend using util.gen_span_id() to generate a span ID, to guarantee that IDs are correctly formatted.	None
parent	Trace | Span[Any] | None	The parent span or trace. If not provided, we will automatically use the current trace/span as the parent.	None
disabled	bool	If True, we will return a Span but the Span will not be recorded.	False
Source code in src/agents/tracing/create.py
mcp_tools_span

mcp_tools_span(
    server: str | None = None,
    result: list[str] | None = None,
    span_id: str | None = None,
    parent: Trace | Span[Any] | None = None,
    disabled: bool = False,
) -> Span[MCPListToolsSpanData]
Create a new MCP list tools span. The span will not be started automatically, you should either do with mcp_tools_span() ... or call span.start() + span.finish() manually.

Parameters:

Name	Type	Description	Default
server	str | None	The name of the MCP server.	None
result	list[str] | None	The result of the MCP list tools call.	None
span_id	str | None	The ID of the span. Optional. If not provided, we will generate an ID. We recommend using util.gen_span_id() to generate a span ID, to guarantee that IDs are correctly formatted.	None
parent	Trace | Span[Any] | None	The parent span or trace. If not provided, we will automatically use the current trace/span as the parent.	None
disabled	bool	If True, we will return a Span but the Span will not be recorded.	False
Source code in src/agents/tracing/create.py