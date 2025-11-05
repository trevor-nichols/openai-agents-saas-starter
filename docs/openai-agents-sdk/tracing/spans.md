Spans
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
NoOpSpan
Bases: Span[TSpanData]

A no-op implementation of Span that doesn't record any data.

Used when tracing is disabled but span operations still need to work.

Parameters:

Name	Type	Description	Default
span_data	TSpanData	The operation-specific data for this span.	required
Source code in src/agents/tracing/spans.py
SpanImpl
Bases: Span[TSpanData]

Source code in src/agents/tracing/spans.py