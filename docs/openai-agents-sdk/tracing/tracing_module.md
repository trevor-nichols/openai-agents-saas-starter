Tracing module
TracingProcessor
Bases: ABC

Interface for processing and monitoring traces and spans in the OpenAI Agents system.

This abstract class defines the interface that all tracing processors must implement. Processors receive notifications when traces and spans start and end, allowing them to collect, process, and export tracing data.

Example

class CustomProcessor(TracingProcessor):
    def __init__(self):
        self.active_traces = {}
        self.active_spans = {}

    def on_trace_start(self, trace):
        self.active_traces[trace.trace_id] = trace

    def on_trace_end(self, trace):
        # Process completed trace
        del self.active_traces[trace.trace_id]

    def on_span_start(self, span):
        self.active_spans[span.span_id] = span

    def on_span_end(self, span):
        # Process completed span
        del self.active_spans[span.span_id]

    def shutdown(self):
        # Clean up resources
        self.active_traces.clear()
        self.active_spans.clear()

    def force_flush(self):
        # Force processing of any queued items
        pass
Notes
All methods should be thread-safe
Methods should not block for long periods
Handle errors gracefully to prevent disrupting agent execution
Source code in src/agents/tracing/processor_interface.py
on_trace_start abstractmethod

on_trace_start(trace: Trace) -> None
Called when a new trace begins execution.

Parameters:

Name	Type	Description	Default
trace	Trace	The trace that started. Contains workflow name and metadata.	required
Notes
Called synchronously on trace start
Should return quickly to avoid blocking execution
Any errors should be caught and handled internally
Source code in src/agents/tracing/processor_interface.py
on_trace_end abstractmethod

on_trace_end(trace: Trace) -> None
Called when a trace completes execution.

Parameters:

Name	Type	Description	Default
trace	Trace	The completed trace containing all spans and results.	required
Notes
Called synchronously when trace finishes
Good time to export/process the complete trace
Should handle cleanup of any trace-specific resources
Source code in src/agents/tracing/processor_interface.py
on_span_start abstractmethod

on_span_start(span: Span[Any]) -> None
Called when a new span begins execution.

Parameters:

Name	Type	Description	Default
span	Span[Any]	The span that started. Contains operation details and context.	required
Notes
Called synchronously on span start
Should return quickly to avoid blocking execution
Spans are automatically nested under current trace/span
Source code in src/agents/tracing/processor_interface.py
on_span_end abstractmethod

on_span_end(span: Span[Any]) -> None
Called when a span completes execution.

Parameters:

Name	Type	Description	Default
span	Span[Any]	The completed span containing execution results.	required
Notes
Called synchronously when span finishes
Should not block or raise exceptions
Good time to export/process the individual span
Source code in src/agents/tracing/processor_interface.py
shutdown abstractmethod

shutdown() -> None
Called when the application stops to clean up resources.

Should perform any necessary cleanup like: - Flushing queued traces/spans - Closing connections - Releasing resources

Source code in src/agents/tracing/processor_interface.py
force_flush abstractmethod

force_flush() -> None
Forces immediate processing of any queued traces/spans.

Notes
Should process all queued items before returning
Useful before shutdown or when immediate processing is needed
May block while processing completes
Source code in src/agents/tracing/processor_interface.py
TraceProvider
Bases: ABC

Interface for creating traces and spans.

Source code in src/agents/tracing/provider.py
register_processor abstractmethod

register_processor(processor: TracingProcessor) -> None
Add a processor that will receive all traces and spans.

Source code in src/agents/tracing/provider.py
set_processors abstractmethod

set_processors(processors: list[TracingProcessor]) -> None
Replace the list of processors with processors.

Source code in src/agents/tracing/provider.py
get_current_trace abstractmethod

get_current_trace() -> Trace | None
Return the currently active trace, if any.

Source code in src/agents/tracing/provider.py
get_current_span abstractmethod

get_current_span() -> Span[Any] | None
Return the currently active span, if any.

Source code in src/agents/tracing/provider.py
set_disabled abstractmethod

set_disabled(disabled: bool) -> None
Enable or disable tracing globally.

Source code in src/agents/tracing/provider.py
time_iso abstractmethod

time_iso() -> str
Return the current time in ISO 8601 format.

Source code in src/agents/tracing/provider.py
gen_trace_id abstractmethod

gen_trace_id() -> str
Generate a new trace identifier.

Source code in src/agents/tracing/provider.py
gen_span_id abstractmethod

gen_span_id() -> str
Generate a new span identifier.

Source code in src/agents/tracing/provider.py
gen_group_id abstractmethod

gen_group_id() -> str
Generate a new group identifier.

Source code in src/agents/tracing/provider.py
create_trace abstractmethod

create_trace(
    name: str,
    trace_id: str | None = None,
    group_id: str | None = None,
    metadata: dict[str, Any] | None = None,
    disabled: bool = False,
) -> Trace
Create a new trace.

Source code in src/agents/tracing/provider.py
create_span abstractmethod

create_span(
    span_data: TSpanData,
    span_id: str | None = None,
    parent: Trace | Span[Any] | None = None,
    disabled: bool = False,
) -> Span[TSpanData]
Create a new span.

Source code in src/agents/tracing/provider.py
shutdown abstractmethod

shutdown() -> None
Clean up any resources used by the provider.

Source code in src/agents/tracing/provider.py
AgentSpanData
Bases: SpanData

Represents an Agent Span in the trace. Includes name, handoffs, tools, and output type.

Source code in src/agents/tracing/span_data.py
CustomSpanData
Bases: SpanData

Represents a Custom Span in the trace. Includes name and data property bag.

Source code in src/agents/tracing/span_data.py
FunctionSpanData
Bases: SpanData

Represents a Function Span in the trace. Includes input, output and MCP data (if applicable).

Source code in src/agents/tracing/span_data.py
GenerationSpanData
Bases: SpanData

Represents a Generation Span in the trace. Includes input, output, model, model configuration, and usage.

Source code in src/agents/tracing/span_data.py
GuardrailSpanData
Bases: SpanData

Represents a Guardrail Span in the trace. Includes name and triggered status.

Source code in src/agents/tracing/span_data.py
HandoffSpanData
Bases: SpanData

Represents a Handoff Span in the trace. Includes source and destination agents.

Source code in src/agents/tracing/span_data.py
MCPListToolsSpanData
Bases: SpanData

Represents an MCP List Tools Span in the trace. Includes server and result.

Source code in src/agents/tracing/span_data.py
ResponseSpanData
Bases: SpanData

Represents a Response Span in the trace. Includes response and input.

Source code in src/agents/tracing/span_data.py
SpanData
Bases: ABC

Represents span data in the trace.

Source code in src/agents/tracing/span_data.py
type abstractmethod property

type: str
Return the type of the span.

export abstractmethod

export() -> dict[str, Any]
Export the span data as a dictionary.

Source code in src/agents/tracing/span_data.py
SpeechGroupSpanData
Bases: SpanData

Represents a Speech Group Span in the trace.

Source code in src/agents/tracing/span_data.py
SpeechSpanData
Bases: SpanData

Represents a Speech Span in the trace. Includes input, output, model, model configuration, and first content timestamp.

Source code in src/agents/tracing/span_data.py
TranscriptionSpanData
Bases: SpanData

Represents a Transcription Span in the trace. Includes input, output, model, and model configuration.

Source code in src/agents/tracing/span_data.py
Span
Bases: ABC, Generic[TSpanData]

Base class for representing traceable operations with timing and context.

A span represents a single operation within a trace (e.g., an LLM call, tool execution, or agent run). Spans track timing, relationships between operations, and operation-specific data.

Example

# Creating a custom span
with custom_span("database_query", {
    "operation": "SELECT",
    "table": "users"
}) as span:
    results = await db.query("SELECT * FROM users")
    span.set_output({"count": len(results)})

# Handling errors in spans
with custom_span("risky_operation") as span:
    try:
        result = perform_risky_operation()
    except Exception as e:
        span.set_error({
            "message": str(e),
            "data": {"operation": "risky_operation"}
        })
        raise
Notes: - Spans automatically nest under the current trace - Use context managers for reliable start/finish - Include relevant data but avoid sensitive information - Handle errors properly using set_error()

Source code in src/agents/tracing/spans.py
trace_id abstractmethod property

trace_id: str
The ID of the trace this span belongs to.

Returns:

Name	Type	Description
str	str	Unique identifier of the parent trace.
span_id abstractmethod property

span_id: str
Unique identifier for this span.

Returns:

Name	Type	Description
str	str	The span's unique ID within its trace.
span_data abstractmethod property

span_data: TSpanData
Operation-specific data for this span.

Returns:

Name	Type	Description
TSpanData	TSpanData	Data specific to this type of span (e.g., LLM generation data).
parent_id abstractmethod property

parent_id: str | None
ID of the parent span, if any.

Returns:

Type	Description
str | None	str | None: The parent span's ID, or None if this is a root span.
error abstractmethod property

error: SpanError | None
Any error that occurred during span execution.

Returns:

Type	Description
SpanError | None	SpanError | None: Error details if an error occurred, None otherwise.
started_at abstractmethod property

started_at: str | None
When the span started execution.

Returns:

Type	Description
str | None	str | None: ISO format timestamp of span start, None if not started.
ended_at abstractmethod property

ended_at: str | None
When the span finished execution.

Returns:

Type	Description
str | None	str | None: ISO format timestamp of span end, None if not finished.
start abstractmethod

start(mark_as_current: bool = False)
Start the span.

Parameters:

Name	Type	Description	Default
mark_as_current	bool	If true, the span will be marked as the current span.	False
Source code in src/agents/tracing/spans.py
finish abstractmethod

finish(reset_current: bool = False) -> None
Finish the span.

Parameters:

Name	Type	Description	Default
reset_current	bool	If true, the span will be reset as the current span.	False
Source code in src/agents/tracing/spans.py
SpanError
Bases: TypedDict

Represents an error that occurred during span execution.

Attributes:

Name	Type	Description
message	str	A human-readable error description
data	dict[str, Any] | None	Optional dictionary containing additional error context
Source code in src/agents/tracing/spans.py
Trace
Bases: ABC

A complete end-to-end workflow containing related spans and metadata.

A trace represents a logical workflow or operation (e.g., "Customer Service Query" or "Code Generation") and contains all the spans (individual operations) that occur during that workflow.

Example

# Basic trace usage
with trace("Order Processing") as t:
    validation_result = await Runner.run(validator, order_data)
    if validation_result.approved:
        await Runner.run(processor, order_data)

# Trace with metadata and grouping
with trace(
    "Customer Service",
    group_id="chat_123",
    metadata={"customer": "user_456"}
) as t:
    result = await Runner.run(support_agent, query)
Notes
Use descriptive workflow names
Group related traces with consistent group_ids
Add relevant metadata for filtering/analysis
Use context managers for reliable cleanup
Consider privacy when adding trace data
Source code in src/agents/tracing/traces.py
trace_id abstractmethod property

trace_id: str
Get the unique identifier for this trace.

Returns:

Name	Type	Description
str	str	The trace's unique ID in the format 'trace_<32_alphanumeric>'
Notes
IDs are globally unique
Used to link spans to their parent trace
Can be used to look up traces in the dashboard
name abstractmethod property

name: str
Get the human-readable name of this workflow trace.

Returns:

Name	Type	Description
str	str	The workflow name (e.g., "Customer Service", "Data Processing")
Notes
Should be descriptive and meaningful
Used for grouping and filtering in the dashboard
Helps identify the purpose of the trace
start abstractmethod

start(mark_as_current: bool = False)
Start the trace and optionally mark it as the current trace.

Parameters:

Name	Type	Description	Default
mark_as_current	bool	If true, marks this trace as the current trace in the execution context.	False
Notes
Must be called before any spans can be added
Only one trace can be current at a time
Thread-safe when using mark_as_current
Source code in src/agents/tracing/traces.py
finish abstractmethod

finish(reset_current: bool = False)
Finish the trace and optionally reset the current trace.

Parameters:

Name	Type	Description	Default
reset_current	bool	If true, resets the current trace to the previous trace in the execution context.	False
Notes
Must be called to complete the trace
Finalizes all open spans
Thread-safe when using reset_current
Source code in src/agents/tracing/traces.py
export abstractmethod

export() -> dict[str, Any] | None
Export the trace data as a serializable dictionary.

Returns:

Type	Description
dict[str, Any] | None	dict | None: Dictionary containing trace data, or None if tracing is disabled.
Notes
Includes all spans and their data
Used for sending traces to backends
May include metadata and group ID
Source code in src/agents/tracing/traces.py
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
get_current_span

get_current_span() -> Span[Any] | None
Returns the currently active span, if present.

Source code in src/agents/tracing/create.py
get_current_trace

get_current_trace() -> Trace | None
Returns the currently active trace, if present.

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
get_trace_provider

get_trace_provider() -> TraceProvider
Get the global trace provider used by tracing utilities.

Source code in src/agents/tracing/setup.py
set_trace_provider

set_trace_provider(provider: TraceProvider) -> None
Set the global trace provider used by tracing utilities.

Source code in src/agents/tracing/setup.py
gen_span_id

gen_span_id() -> str
Generate a new span ID.

Source code in src/agents/tracing/util.py
gen_trace_id

gen_trace_id() -> str
Generate a new trace ID.

Source code in src/agents/tracing/util.py
add_trace_processor

add_trace_processor(
    span_processor: TracingProcessor,
) -> None
Adds a new trace processor. This processor will receive all traces/spans.

Source code in src/agents/tracing/__init__.py
set_trace_processors

set_trace_processors(
    processors: list[TracingProcessor],
) -> None
Set the list of trace processors. This will replace the current list of processors.

Source code in src/agents/tracing/__init__.py
set_tracing_disabled

set_tracing_disabled(disabled: bool) -> None
Set whether tracing is globally disabled.

Source code in src/agents/tracing/__init__.py
set_tracing_export_api_key

set_tracing_export_api_key(api_key: str) -> None
Set the OpenAI API key for the backend exporter.

Source code in src/agents/tracing/__init__.py