Agents
ToolsToFinalOutputFunction module-attribute

ToolsToFinalOutputFunction: TypeAlias = Callable[
    [RunContextWrapper[TContext], list[FunctionToolResult]],
    MaybeAwaitable[ToolsToFinalOutputResult],
]
A function that takes a run context and a list of tool results, and returns a ToolsToFinalOutputResult.

ToolsToFinalOutputResult dataclass
Source code in src/agents/agent.py
is_final_output instance-attribute

is_final_output: bool
Whether this is the final output. If False, the LLM will run again and receive the tool call output.

final_output class-attribute instance-attribute

final_output: Any | None = None
The final output. Can be None if is_final_output is False, otherwise must match the output_type of the agent.

StopAtTools
Bases: TypedDict

Source code in src/agents/agent.py
stop_at_tool_names instance-attribute

stop_at_tool_names: list[str]
A list of tool names, any of which will stop the agent from running further.

MCPConfig
Bases: TypedDict

Configuration for MCP servers.

Source code in src/agents/agent.py
convert_schemas_to_strict instance-attribute

convert_schemas_to_strict: NotRequired[bool]
If True, we will attempt to convert the MCP schemas to strict-mode schemas. This is a best-effort conversion, so some schemas may not be convertible. Defaults to False.

AgentBase dataclass
Bases: Generic[TContext]

Base class for Agent and RealtimeAgent.

Source code in src/agents/agent.py
name instance-attribute

name: str
The name of the agent.

handoff_description class-attribute instance-attribute

handoff_description: str | None = None
A description of the agent. This is used when the agent is used as a handoff, so that an LLM knows what it does and when to invoke it.

tools class-attribute instance-attribute

tools: list[Tool] = field(default_factory=list)
A list of tools that the agent can use.

mcp_servers class-attribute instance-attribute

mcp_servers: list[MCPServer] = field(default_factory=list)
A list of Model Context Protocol servers that the agent can use. Every time the agent runs, it will include tools from these servers in the list of available tools.

NOTE: You are expected to manage the lifecycle of these servers. Specifically, you must call server.connect() before passing it to the agent, and server.cleanup() when the server is no longer needed.

mcp_config class-attribute instance-attribute

mcp_config: MCPConfig = field(
    default_factory=lambda: MCPConfig()
)
Configuration for MCP servers.

get_mcp_tools async

get_mcp_tools(
    run_context: RunContextWrapper[TContext],
) -> list[Tool]
Fetches the available tools from the MCP servers.

Source code in src/agents/agent.py
get_all_tools async

get_all_tools(
    run_context: RunContextWrapper[TContext],
) -> list[Tool]
All agent tools, including MCP tools and function tools.

Source code in src/agents/agent.py
Agent dataclass
Bases: AgentBase, Generic[TContext]

An agent is an AI model configured with instructions, tools, guardrails, handoffs and more.

We strongly recommend passing instructions, which is the "system prompt" for the agent. In addition, you can pass handoff_description, which is a human-readable description of the agent, used when the agent is used inside tools/handoffs.

Agents are generic on the context type. The context is a (mutable) object you create. It is passed to tool functions, handoffs, guardrails, etc.

See AgentBase for base parameters that are shared with RealtimeAgents.

Source code in src/agents/agent.py
instructions class-attribute instance-attribute

instructions: (
    str
    | Callable[
        [RunContextWrapper[TContext], Agent[TContext]],
        MaybeAwaitable[str],
    ]
    | None
) = None
The instructions for the agent. Will be used as the "system prompt" when this agent is invoked. Describes what the agent should do, and how it responds.

Can either be a string, or a function that dynamically generates instructions for the agent. If you provide a function, it will be called with the context and the agent instance. It must return a string.

prompt class-attribute instance-attribute

prompt: Prompt | DynamicPromptFunction | None = None
A prompt object (or a function that returns a Prompt). Prompts allow you to dynamically configure the instructions, tools and other config for an agent outside of your code. Only usable with OpenAI models, using the Responses API.

handoffs class-attribute instance-attribute

handoffs: list[Agent[Any] | Handoff[TContext, Any]] = field(
    default_factory=list
)
Handoffs are sub-agents that the agent can delegate to. You can provide a list of handoffs, and the agent can choose to delegate to them if relevant. Allows for separation of concerns and modularity.

model class-attribute instance-attribute

model: str | Model | None = None
The model implementation to use when invoking the LLM.

By default, if not set, the agent will use the default model configured in agents.models.get_default_model() (currently "gpt-4.1").

model_settings class-attribute instance-attribute

model_settings: ModelSettings = field(
    default_factory=get_default_model_settings
)
Configures model-specific tuning parameters (e.g. temperature, top_p).

input_guardrails class-attribute instance-attribute

input_guardrails: list[InputGuardrail[TContext]] = field(
    default_factory=list
)
A list of checks that run in parallel to the agent's execution, before generating a response. Runs only if the agent is the first agent in the chain.

output_guardrails class-attribute instance-attribute

output_guardrails: list[OutputGuardrail[TContext]] = field(
    default_factory=list
)
A list of checks that run on the final output of the agent, after generating a response. Runs only if the agent produces a final output.

output_type class-attribute instance-attribute

output_type: type[Any] | AgentOutputSchemaBase | None = None
The type of the output object. If not provided, the output will be str. In most cases, you should pass a regular Python type (e.g. a dataclass, Pydantic model, TypedDict, etc). You can customize this in two ways: 1. If you want non-strict schemas, pass AgentOutputSchema(MyClass, strict_json_schema=False). 2. If you want to use a custom JSON schema (i.e. without using the SDK's automatic schema) creation, subclass and pass an AgentOutputSchemaBase subclass.

hooks class-attribute instance-attribute

hooks: AgentHooks[TContext] | None = None
A class that receives callbacks on various lifecycle events for this agent.

tool_use_behavior class-attribute instance-attribute

tool_use_behavior: (
    Literal["run_llm_again", "stop_on_first_tool"]
    | StopAtTools
    | ToolsToFinalOutputFunction
) = "run_llm_again"
This lets you configure how tool use is handled. - "run_llm_again": The default behavior. Tools are run, and then the LLM receives the results and gets to respond. - "stop_on_first_tool": The output from the first tool call is treated as the final result. In other words, it isn’t sent back to the LLM for further processing but is used directly as the final output. - A StopAtTools object: The agent will stop running if any of the tools listed in stop_at_tool_names is called. The final output will be the output of the first matching tool call. The LLM does not process the result of the tool call. - A function: If you pass a function, it will be called with the run context and the list of tool results. It must return a ToolsToFinalOutputResult, which determines whether the tool calls result in a final output.

NOTE: This configuration is specific to FunctionTools. Hosted tools, such as file search, web search, etc. are always processed by the LLM.

reset_tool_choice class-attribute instance-attribute

reset_tool_choice: bool = True
Whether to reset the tool choice to the default value after a tool has been called. Defaults to True. This ensures that the agent doesn't enter an infinite loop of tool usage.

name instance-attribute

name: str
The name of the agent.

handoff_description class-attribute instance-attribute

handoff_description: str | None = None
A description of the agent. This is used when the agent is used as a handoff, so that an LLM knows what it does and when to invoke it.

tools class-attribute instance-attribute

tools: list[Tool] = field(default_factory=list)
A list of tools that the agent can use.

mcp_servers class-attribute instance-attribute

mcp_servers: list[MCPServer] = field(default_factory=list)
A list of Model Context Protocol servers that the agent can use. Every time the agent runs, it will include tools from these servers in the list of available tools.

NOTE: You are expected to manage the lifecycle of these servers. Specifically, you must call server.connect() before passing it to the agent, and server.cleanup() when the server is no longer needed.

mcp_config class-attribute instance-attribute

mcp_config: MCPConfig = field(
    default_factory=lambda: MCPConfig()
)
Configuration for MCP servers.

clone

clone(**kwargs: Any) -> Agent[TContext]
Make a copy of the agent, with the given arguments changed. Notes: - Uses dataclasses.replace, which performs a shallow copy. - Mutable attributes like tools and handoffs are shallow-copied: new list objects are created only if overridden, but their contents (tool functions and handoff objects) are shared with the original. - To modify these independently, pass new lists when calling clone(). Example:


new_agent = agent.clone(instructions="New instructions")
Source code in src/agents/agent.py
as_tool

as_tool(
    tool_name: str | None,
    tool_description: str | None,
    custom_output_extractor: Callable[
        [RunResult], Awaitable[str]
    ]
    | None = None,
    is_enabled: bool
    | Callable[
        [RunContextWrapper[Any], AgentBase[Any]],
        MaybeAwaitable[bool],
    ] = True,
    run_config: RunConfig | None = None,
    max_turns: int | None = None,
    hooks: RunHooks[TContext] | None = None,
    previous_response_id: str | None = None,
    conversation_id: str | None = None,
    session: Session | None = None,
) -> Tool
Transform this agent into a tool, callable by other agents.

This is different from handoffs in two ways: 1. In handoffs, the new agent receives the conversation history. In this tool, the new agent receives generated input. 2. In handoffs, the new agent takes over the conversation. In this tool, the new agent is called as a tool, and the conversation is continued by the original agent.

Parameters:

Name	Type	Description	Default
tool_name	str | None	The name of the tool. If not provided, the agent's name will be used.	required
tool_description	str | None	The description of the tool, which should indicate what it does and when to use it.	required
custom_output_extractor	Callable[[RunResult], Awaitable[str]] | None	A function that extracts the output from the agent. If not provided, the last message from the agent will be used.	None
is_enabled	bool | Callable[[RunContextWrapper[Any], AgentBase[Any]], MaybeAwaitable[bool]]	Whether the tool is enabled. Can be a bool or a callable that takes the run context and agent and returns whether the tool is enabled. Disabled tools are hidden from the LLM at runtime.	True
Source code in src/agents/agent.py
get_prompt async

get_prompt(
    run_context: RunContextWrapper[TContext],
) -> ResponsePromptParam | None
Get the prompt for the agent.

Source code in src/agents/agent.py
get_mcp_tools async

get_mcp_tools(
    run_context: RunContextWrapper[TContext],
) -> list[Tool]
Fetches the available tools from the MCP servers.

Source code in src/agents/agent.py
get_all_tools async

get_all_tools(
    run_context: RunContextWrapper[TContext],
) -> list[Tool]
All agent tools, including MCP tools and function tools.

Source code in src/agents/agent.py