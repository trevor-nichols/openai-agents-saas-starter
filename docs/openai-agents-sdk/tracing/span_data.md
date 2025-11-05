Span data
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
AgentSpanData
Bases: SpanData

Represents an Agent Span in the trace. Includes name, handoffs, tools, and output type.

Source code in src/agents/tracing/span_data.py
FunctionSpanData
Bases: SpanData

Represents a Function Span in the trace. Includes input, output and MCP data (if applicable).

Source code in src/agents/tracing/span_data.py
GenerationSpanData
Bases: SpanData

Represents a Generation Span in the trace. Includes input, output, model, model configuration, and usage.

Source code in src/agents/tracing/span_data.py
ResponseSpanData
Bases: SpanData

Represents a Response Span in the trace. Includes response and input.

Source code in src/agents/tracing/span_data.py
HandoffSpanData
Bases: SpanData

Represents a Handoff Span in the trace. Includes source and destination agents.

Source code in src/agents/tracing/span_data.py
CustomSpanData
Bases: SpanData

Represents a Custom Span in the trace. Includes name and data property bag.

Source code in src/agents/tracing/span_data.py
GuardrailSpanData
Bases: SpanData

Represents a Guardrail Span in the trace. Includes name and triggered status.

Source code in src/agents/tracing/span_data.py
TranscriptionSpanData
Bases: SpanData

Represents a Transcription Span in the trace. Includes input, output, model, and model configuration.

Source code in src/agents/tracing/span_data.py
SpeechSpanData
Bases: SpanData

Represents a Speech Span in the trace. Includes input, output, model, model configuration, and first content timestamp.

Source code in src/agents/tracing/span_data.py
SpeechGroupSpanData
Bases: SpanData

Represents a Speech Group Span in the trace.

Source code in src/agents/tracing/span_data.py
MCPListToolsSpanData
Bases: SpanData

Represents an MCP List Tools Span in the trace. Includes server and result.

Source code in src/agents/tracing/span_data.py