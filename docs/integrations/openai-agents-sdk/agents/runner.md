Runner
Runner
Source code in src/agents/run.py
run async classmethod

run(
    starting_agent: Agent[TContext],
    input: str | list[TResponseInputItem],
    *,
    context: TContext | None = None,
    max_turns: int = DEFAULT_MAX_TURNS,
    hooks: RunHooks[TContext] | None = None,
    run_config: RunConfig | None = None,
    previous_response_id: str | None = None,
    conversation_id: str | None = None,
    session: Session | None = None,
) -> RunResult
Run a workflow starting at the given agent.

The agent will run in a loop until a final output is generated. The loop runs like so:

The agent is invoked with the given input.
If there is a final output (i.e. the agent produces something of type agent.output_type), the loop terminates.
If there's a handoff, we run the loop again, with the new agent.
Else, we run tool calls (if any), and re-run the loop.
In two cases, the agent may raise an exception:

If the max_turns is exceeded, a MaxTurnsExceeded exception is raised.
If a guardrail tripwire is triggered, a GuardrailTripwireTriggered exception is raised.
Note
Only the first agent's input guardrails are run.

Parameters:

Name	Type	Description	Default
starting_agent	Agent[TContext]	The starting agent to run.	required
input	str | list[TResponseInputItem]	The initial input to the agent. You can pass a single string for a user message, or a list of input items.	required
context	TContext | None	The context to run the agent with.	None
max_turns	int	The maximum number of turns to run the agent for. A turn is defined as one AI invocation (including any tool calls that might occur).	DEFAULT_MAX_TURNS
hooks	RunHooks[TContext] | None	An object that receives callbacks on various lifecycle events.	None
run_config	RunConfig | None	Global settings for the entire agent run.	None
previous_response_id	str | None	The ID of the previous response. If using OpenAI models via the Responses API, this allows you to skip passing in input from the previous turn.	None
conversation_id	str | None	The conversation ID (https://platform.openai.com/docs/guides/conversation-state?api-mode=responses). If provided, the conversation will be used to read and write items. Every agent will have access to the conversation history so far, and its output items will be written to the conversation. We recommend only using this if you are exclusively using OpenAI models; other model providers don't write to the Conversation object, so you'll end up having partial conversations stored.	None
session	Session | None	A session for automatic conversation history management.	None
Returns:

Type	Description
RunResult	A run result containing all the inputs, guardrail results and the output of
RunResult	the last agent. Agents may perform handoffs, so we don't know the specific
RunResult	type of the output.
Source code in src/agents/run.py
run_sync classmethod

run_sync(
    starting_agent: Agent[TContext],
    input: str | list[TResponseInputItem],
    *,
    context: TContext | None = None,
    max_turns: int = DEFAULT_MAX_TURNS,
    hooks: RunHooks[TContext] | None = None,
    run_config: RunConfig | None = None,
    previous_response_id: str | None = None,
    conversation_id: str | None = None,
    session: Session | None = None,
) -> RunResult
Run a workflow synchronously, starting at the given agent.

Note
This just wraps the run method, so it will not work if there's already an event loop (e.g. inside an async function, or in a Jupyter notebook or async context like FastAPI). For those cases, use the run method instead.

The agent will run in a loop until a final output is generated. The loop runs:

The agent is invoked with the given input.
If there is a final output (i.e. the agent produces something of type agent.output_type), the loop terminates.
If there's a handoff, we run the loop again, with the new agent.
Else, we run tool calls (if any), and re-run the loop.
In two cases, the agent may raise an exception:

If the max_turns is exceeded, a MaxTurnsExceeded exception is raised.
If a guardrail tripwire is triggered, a GuardrailTripwireTriggered exception is raised.
Note
Only the first agent's input guardrails are run.

Parameters:

Name	Type	Description	Default
starting_agent	Agent[TContext]	The starting agent to run.	required
input	str | list[TResponseInputItem]	The initial input to the agent. You can pass a single string for a user message, or a list of input items.	required
context	TContext | None	The context to run the agent with.	None
max_turns	int	The maximum number of turns to run the agent for. A turn is defined as one AI invocation (including any tool calls that might occur).	DEFAULT_MAX_TURNS
hooks	RunHooks[TContext] | None	An object that receives callbacks on various lifecycle events.	None
run_config	RunConfig | None	Global settings for the entire agent run.	None
previous_response_id	str | None	The ID of the previous response, if using OpenAI models via the Responses API, this allows you to skip passing in input from the previous turn.	None
conversation_id	str | None	The ID of the stored conversation, if any.	None
session	Session | None	A session for automatic conversation history management.	None
Returns:

Type	Description
RunResult	A run result containing all the inputs, guardrail results and the output of
RunResult	the last agent. Agents may perform handoffs, so we don't know the specific
RunResult	type of the output.
Source code in src/agents/run.py
run_streamed classmethod

run_streamed(
    starting_agent: Agent[TContext],
    input: str | list[TResponseInputItem],
    context: TContext | None = None,
    max_turns: int = DEFAULT_MAX_TURNS,
    hooks: RunHooks[TContext] | None = None,
    run_config: RunConfig | None = None,
    previous_response_id: str | None = None,
    conversation_id: str | None = None,
    session: Session | None = None,
) -> RunResultStreaming
Run a workflow starting at the given agent in streaming mode.

The returned result object contains a method you can use to stream semantic events as they are generated.

The agent will run in a loop until a final output is generated. The loop runs like so:

The agent is invoked with the given input.
If there is a final output (i.e. the agent produces something of type agent.output_type), the loop terminates.
If there's a handoff, we run the loop again, with the new agent.
Else, we run tool calls (if any), and re-run the loop.
In two cases, the agent may raise an exception:

If the max_turns is exceeded, a MaxTurnsExceeded exception is raised.
If a guardrail tripwire is triggered, a GuardrailTripwireTriggered exception is raised.
Note
Only the first agent's input guardrails are run.

Parameters:

Name	Type	Description	Default
starting_agent	Agent[TContext]	The starting agent to run.	required
input	str | list[TResponseInputItem]	The initial input to the agent. You can pass a single string for a user message, or a list of input items.	required
context	TContext | None	The context to run the agent with.	None
max_turns	int	The maximum number of turns to run the agent for. A turn is defined as one AI invocation (including any tool calls that might occur).	DEFAULT_MAX_TURNS
hooks	RunHooks[TContext] | None	An object that receives callbacks on various lifecycle events.	None
run_config	RunConfig | None	Global settings for the entire agent run.	None
previous_response_id	str | None	The ID of the previous response, if using OpenAI models via the Responses API, this allows you to skip passing in input from the previous turn.	None
conversation_id	str | None	The ID of the stored conversation, if any.	None
session	Session | None	A session for automatic conversation history management.	None
Returns:

Type	Description
RunResultStreaming	A result object that contains data about the run, as well as a method to
RunResultStreaming	stream events.
Source code in src/agents/run.py
RunConfig dataclass
Configures settings for the entire agent run.

Source code in src/agents/run.py
model class-attribute instance-attribute

model: str | Model | None = None
The model to use for the entire agent run. If set, will override the model set on every agent. The model_provider passed in below must be able to resolve this model name.

model_provider class-attribute instance-attribute

model_provider: ModelProvider = field(
    default_factory=MultiProvider
)
The model provider to use when looking up string model names. Defaults to OpenAI.

model_settings class-attribute instance-attribute

model_settings: ModelSettings | None = None
Configure global model settings. Any non-null values will override the agent-specific model settings.

handoff_input_filter class-attribute instance-attribute

handoff_input_filter: HandoffInputFilter | None = None
A global input filter to apply to all handoffs. If Handoff.input_filter is set, then that will take precedence. The input filter allows you to edit the inputs that are sent to the new agent. See the documentation in Handoff.input_filter for more details.

input_guardrails class-attribute instance-attribute

input_guardrails: list[InputGuardrail[Any]] | None = None
A list of input guardrails to run on the initial run input.

output_guardrails class-attribute instance-attribute

output_guardrails: list[OutputGuardrail[Any]] | None = None
A list of output guardrails to run on the final output of the run.

tracing_disabled class-attribute instance-attribute

tracing_disabled: bool = False
Whether tracing is disabled for the agent run. If disabled, we will not trace the agent run.

trace_include_sensitive_data class-attribute instance-attribute

trace_include_sensitive_data: bool = field(
    default_factory=_default_trace_include_sensitive_data
)
Whether we include potentially sensitive data (for example: inputs/outputs of tool calls or LLM generations) in traces. If False, we'll still create spans for these events, but the sensitive data will not be included.

workflow_name class-attribute instance-attribute

workflow_name: str = 'Agent workflow'
The name of the run, used for tracing. Should be a logical name for the run, like "Code generation workflow" or "Customer support agent".

trace_id class-attribute instance-attribute

trace_id: str | None = None
A custom trace ID to use for tracing. If not provided, we will generate a new trace ID.

group_id class-attribute instance-attribute

group_id: str | None = None
A grouping identifier to use for tracing, to link multiple traces from the same conversation or process. For example, you might use a chat thread ID.

trace_metadata class-attribute instance-attribute

trace_metadata: dict[str, Any] | None = None
An optional dictionary of additional metadata to include with the trace.

session_input_callback class-attribute instance-attribute

session_input_callback: SessionInputCallback | None = None
Defines how to handle session history when new input is provided. - None (default): The new input is appended to the session history. - SessionInputCallback: A custom function that receives the history and new input, and returns the desired combined list of items.

call_model_input_filter class-attribute instance-attribute

call_model_input_filter: CallModelInputFilter | None = None
Optional callback that is invoked immediately before calling the model. It receives the current agent, context and the model input (instructions and input items), and must return a possibly modified ModelInputData to use for the model call.

This allows you to edit the input sent to the model e.g. to stay within a token limit. For example, you can use this to add a system prompt to the input.