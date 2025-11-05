Handoffs
HandoffInputFilter module-attribute

HandoffInputFilter: TypeAlias = Callable[
    [HandoffInputData], MaybeAwaitable[HandoffInputData]
]
A function that filters the input data passed to the next agent.

HandoffInputData dataclass
Source code in src/agents/handoffs.py
input_history instance-attribute

input_history: str | tuple[TResponseInputItem, ...]
The input history before Runner.run() was called.

pre_handoff_items instance-attribute

pre_handoff_items: tuple[RunItem, ...]
The items generated before the agent turn where the handoff was invoked.

new_items instance-attribute

new_items: tuple[RunItem, ...]
The new items generated during the current agent turn, including the item that triggered the handoff and the tool output message representing the response from the handoff output.

run_context class-attribute instance-attribute

run_context: RunContextWrapper[Any] | None = None
The run context at the time the handoff was invoked. Note that, since this property was added later on, it's optional for backwards compatibility.

clone

clone(**kwargs: Any) -> HandoffInputData
Make a copy of the handoff input data, with the given arguments changed. For example, you could do:


new_handoff_input_data = handoff_input_data.clone(new_items=())
Source code in src/agents/handoffs.py
Handoff dataclass
Bases: Generic[TContext, TAgent]

A handoff is when an agent delegates a task to another agent. For example, in a customer support scenario you might have a "triage agent" that determines which agent should handle the user's request, and sub-agents that specialize in different areas like billing, account management, etc.

Source code in src/agents/handoffs.py
tool_name instance-attribute

tool_name: str
The name of the tool that represents the handoff.

tool_description instance-attribute

tool_description: str
The description of the tool that represents the handoff.

input_json_schema instance-attribute

input_json_schema: dict[str, Any]
The JSON schema for the handoff input. Can be empty if the handoff does not take an input.

on_invoke_handoff instance-attribute

on_invoke_handoff: Callable[
    [RunContextWrapper[Any], str], Awaitable[TAgent]
]
The function that invokes the handoff. The parameters passed are: 1. The handoff run context 2. The arguments from the LLM, as a JSON string. Empty string if input_json_schema is empty.

Must return an agent.

agent_name instance-attribute

agent_name: str
The name of the agent that is being handed off to.

input_filter class-attribute instance-attribute

input_filter: HandoffInputFilter | None = None
A function that filters the inputs that are passed to the next agent. By default, the new agent sees the entire conversation history. In some cases, you may want to filter inputs e.g. to remove older inputs, or remove tools from existing inputs.

The function will receive the entire conversation history so far, including the input item that triggered the handoff and a tool call output item representing the handoff tool's output.

You are free to modify the input history or new items as you see fit. The next agent that runs will receive handoff_input_data.all_items.

IMPORTANT: in streaming mode, we will not stream anything as a result of this function. The items generated before will already have been streamed.

strict_json_schema class-attribute instance-attribute

strict_json_schema: bool = True
Whether the input JSON schema is in strict mode. We strongly recommend setting this to True, as it increases the likelihood of correct JSON input.

is_enabled class-attribute instance-attribute

is_enabled: (
    bool
    | Callable[
        [RunContextWrapper[Any], AgentBase[Any]],
        MaybeAwaitable[bool],
    ]
) = True
Whether the handoff is enabled. Either a bool or a Callable that takes the run context and agent and returns whether the handoff is enabled. You can use this to dynamically enable/disable a handoff based on your context/state.

handoff

handoff(
    agent: Agent[TContext],
    *,
    tool_name_override: str | None = None,
    tool_description_override: str | None = None,
    input_filter: Callable[
        [HandoffInputData], HandoffInputData
    ]
    | None = None,
    is_enabled: bool
    | Callable[
        [RunContextWrapper[Any], Agent[Any]],
        MaybeAwaitable[bool],
    ] = True,
) -> Handoff[TContext, Agent[TContext]]

handoff(
    agent: Agent[TContext],
    *,
    on_handoff: OnHandoffWithInput[THandoffInput],
    input_type: type[THandoffInput],
    tool_description_override: str | None = None,
    tool_name_override: str | None = None,
    input_filter: Callable[
        [HandoffInputData], HandoffInputData
    ]
    | None = None,
    is_enabled: bool
    | Callable[
        [RunContextWrapper[Any], Agent[Any]],
        MaybeAwaitable[bool],
    ] = True,
) -> Handoff[TContext, Agent[TContext]]

handoff(
    agent: Agent[TContext],
    *,
    on_handoff: OnHandoffWithoutInput,
    tool_description_override: str | None = None,
    tool_name_override: str | None = None,
    input_filter: Callable[
        [HandoffInputData], HandoffInputData
    ]
    | None = None,
    is_enabled: bool
    | Callable[
        [RunContextWrapper[Any], Agent[Any]],
        MaybeAwaitable[bool],
    ] = True,
) -> Handoff[TContext, Agent[TContext]]

handoff(
    agent: Agent[TContext],
    tool_name_override: str | None = None,
    tool_description_override: str | None = None,
    on_handoff: OnHandoffWithInput[THandoffInput]
    | OnHandoffWithoutInput
    | None = None,
    input_type: type[THandoffInput] | None = None,
    input_filter: Callable[
        [HandoffInputData], HandoffInputData
    ]
    | None = None,
    is_enabled: bool
    | Callable[
        [RunContextWrapper[Any], Agent[TContext]],
        MaybeAwaitable[bool],
    ] = True,
) -> Handoff[TContext, Agent[TContext]]
Create a handoff from an agent.

Parameters:

Name	Type	Description	Default
agent	Agent[TContext]	The agent to handoff to, or a function that returns an agent.	required
tool_name_override	str | None	Optional override for the name of the tool that represents the handoff.	None
tool_description_override	str | None	Optional override for the description of the tool that represents the handoff.	None
on_handoff	OnHandoffWithInput[THandoffInput] | OnHandoffWithoutInput | None	A function that runs when the handoff is invoked.	None
input_type	type[THandoffInput] | None	the type of the input to the handoff. If provided, the input will be validated against this type. Only relevant if you pass a function that takes an input.	None
input_filter	Callable[[HandoffInputData], HandoffInputData] | None	a function that filters the inputs that are passed to the next agent.	None
is_enabled	bool | Callable[[RunContextWrapper[Any], Agent[TContext]], MaybeAwaitable[bool]]	Whether the handoff is enabled. Can be a bool or a callable that takes the run context and agent and returns whether the handoff is enabled. Disabled handoffs are hidden from the LLM at runtime.	True
Source code in src/agents/handoffs.py
