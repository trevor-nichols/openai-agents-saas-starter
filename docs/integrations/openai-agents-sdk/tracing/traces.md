Traces
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
NoOpTrace
Bases: Trace

A no-op implementation of Trace that doesn't record any data.

Used when tracing is disabled but trace operations still need to work. Maintains proper context management but doesn't store or export any data.

Example

# When tracing is disabled, traces become NoOpTrace
with trace("Disabled Workflow") as t:
    # Operations still work but nothing is recorded
    await Runner.run(agent, "query")
Source code in src/agents/tracing/traces.py
trace_id property

trace_id: str
The trace's unique identifier.

Returns:

Name	Type	Description
str	str	A unique ID for this trace.
name property

name: str
The workflow name for this trace.

Returns:

Name	Type	Description
str	str	Human-readable name describing this workflow.
export

export() -> dict[str, Any] | None
Export the trace data as a dictionary.

Returns:

Type	Description
dict[str, Any] | None	dict | None: Trace data in exportable format, or None if no data.
Source code in src/agents/tracing/traces.py
TraceImpl
Bases: Trace

A trace that will be recorded by the tracing library.

Source code in src/agents/tracing/traces.py