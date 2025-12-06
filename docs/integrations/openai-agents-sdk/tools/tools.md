Tools
MCPToolApprovalFunction module-attribute

MCPToolApprovalFunction = Callable[
    [MCPToolApprovalRequest],
    MaybeAwaitable[MCPToolApprovalFunctionResult],
]
A function that approves or rejects a tool call.

LocalShellExecutor module-attribute

LocalShellExecutor = Callable[
    [LocalShellCommandRequest], MaybeAwaitable[str]
]
A function that executes a command on a shell.

Tool module-attribute

Tool = Union[
    FunctionTool,
    FileSearchTool,
    WebSearchTool,
    ComputerTool,
    HostedMCPTool,
    LocalShellTool,
    ImageGenerationTool,
    CodeInterpreterTool,
]
A tool that can be used in an agent.

## Tool assignment in this starter

We mirror the OpenAI Agents SDK pattern directly: each `AgentSpec` declares an
explicit, ordered `tool_keys` tuple, and `OpenAIAgentRegistry` resolves those
keys from the `ToolRegistry` at startup. There is **no** core/automatic inclusion
or capability-based filtering anymore; missing required tools fail fast during
agent build. Optional tools (e.g., `web_search` when `OPENAI_API_KEY` is absent)
log a warning and are skipped.

Adding a tool means:
1. Register it once in `initialize_tools()` with a stable name.
2. Add that name to the desired agent’s `tool_keys`.
3. (Optional) pass runtime customizations (like `user_location`) in `_select_tools`.

FunctionToolResult dataclass
Source code in src/agents/tool.py
tool instance-attribute

tool: FunctionTool
The tool that was run.

output instance-attribute

output: Any
The output of the tool.

run_item instance-attribute

run_item: RunItem
The run item that was produced as a result of the tool call.

FunctionTool dataclass
A tool that wraps a function. In most cases, you should use the function_tool helpers to create a FunctionTool, as they let you easily wrap a Python function.

Source code in src/agents/tool.py
name instance-attribute

name: str
The name of the tool, as shown to the LLM. Generally the name of the function.

description instance-attribute

description: str
A description of the tool, as shown to the LLM.

params_json_schema instance-attribute

params_json_schema: dict[str, Any]
The JSON schema for the tool's parameters.

on_invoke_tool instance-attribute

on_invoke_tool: Callable[
    [ToolContext[Any], str], Awaitable[Any]
]
A function that invokes the tool with the given context and parameters. The params passed are: 1. The tool run context. 2. The arguments from the LLM, as a JSON string.

You must return a string representation of the tool output, or something we can call str() on. In case of errors, you can either raise an Exception (which will cause the run to fail) or return a string error message (which will be sent back to the LLM).

strict_json_schema class-attribute instance-attribute

strict_json_schema: bool = True
Whether the JSON schema is in strict mode. We strongly recommend setting this to True, as it increases the likelihood of correct JSON input.

is_enabled class-attribute instance-attribute

is_enabled: (
    bool
    | Callable[
        [RunContextWrapper[Any], AgentBase],
        MaybeAwaitable[bool],
    ]
) = True
Whether the tool is enabled. Either a bool or a Callable that takes the run context and agent and returns whether the tool is enabled. You can use this to dynamically enable/disable a tool based on your context/state.

FileSearchTool dataclass
A hosted tool that lets the LLM search through a vector store. Currently only supported with OpenAI models, using the Responses API.

Source code in src/agents/tool.py
vector_store_ids instance-attribute

vector_store_ids: list[str]
The IDs of the vector stores to search.

max_num_results class-attribute instance-attribute

max_num_results: int | None = None
The maximum number of results to return.

include_search_results class-attribute instance-attribute

include_search_results: bool = False
Whether to include the search results in the output produced by the LLM.

ranking_options class-attribute instance-attribute

ranking_options: RankingOptions | None = None
Ranking options for search.

filters class-attribute instance-attribute

filters: Filters | None = None
A filter to apply based on file attributes.

WebSearchTool dataclass
A hosted tool that lets the LLM search the web. Currently only supported with OpenAI models, using the Responses API.

Source code in src/agents/tool.py
user_location class-attribute instance-attribute

user_location: UserLocation | None = None
Optional location for the search. Lets you customize results to be relevant to a location.

filters class-attribute instance-attribute

filters: Filters | None = None
A filter to apply based on file attributes.

search_context_size class-attribute instance-attribute

search_context_size: Literal["low", "medium", "high"] = (
    "medium"
)
The amount of context to use for the search.

ComputerTool dataclass
A hosted tool that lets the LLM control a computer.

Source code in src/agents/tool.py
computer instance-attribute

computer: Computer | AsyncComputer
The computer implementation, which describes the environment and dimensions of the computer, as well as implements the computer actions like click, screenshot, etc.

on_safety_check class-attribute instance-attribute

on_safety_check: (
    Callable[
        [ComputerToolSafetyCheckData], MaybeAwaitable[bool]
    ]
    | None
) = None
Optional callback to acknowledge computer tool safety checks.

ComputerToolSafetyCheckData dataclass
Information about a computer tool safety check.

Source code in src/agents/tool.py
ctx_wrapper instance-attribute

ctx_wrapper: RunContextWrapper[Any]
The run context.

agent instance-attribute

agent: Agent[Any]
The agent performing the computer action.

tool_call instance-attribute

tool_call: ResponseComputerToolCall
The computer tool call.

safety_check instance-attribute

safety_check: PendingSafetyCheck
The pending safety check to acknowledge.

MCPToolApprovalRequest dataclass
A request to approve a tool call.

Source code in src/agents/tool.py
ctx_wrapper instance-attribute

ctx_wrapper: RunContextWrapper[Any]
The run context.

data instance-attribute

data: McpApprovalRequest
The data from the MCP tool approval request.

MCPToolApprovalFunctionResult
Bases: TypedDict

The result of an MCP tool approval function.

Source code in src/agents/tool.py
approve instance-attribute

approve: bool
Whether to approve the tool call.

reason instance-attribute

reason: NotRequired[str]
An optional reason, if rejected.

HostedMCPTool dataclass
A tool that allows the LLM to use a remote MCP server. The LLM will automatically list and call tools, without requiring a round trip back to your code. If you want to run MCP servers locally via stdio, in a VPC or other non-publicly-accessible environment, or you just prefer to run tool calls locally, then you can instead use the servers in agents.mcp and pass Agent(mcp_servers=[...]) to the agent.

Source code in src/agents/tool.py
tool_config instance-attribute

tool_config: Mcp
The MCP tool config, which includes the server URL and other settings.

on_approval_request class-attribute instance-attribute

on_approval_request: MCPToolApprovalFunction | None = None
An optional function that will be called if approval is requested for an MCP tool. If not provided, you will need to manually add approvals/rejections to the input and call Runner.run(...) again.

CodeInterpreterTool dataclass
A tool that allows the LLM to execute code in a sandboxed environment.

Source code in src/agents/tool.py
tool_config instance-attribute

tool_config: CodeInterpreter
The tool config, which includes the container and other settings.

ImageGenerationTool dataclass
A tool that allows the LLM to generate images.

Source code in src/agents/tool.py
tool_config instance-attribute

tool_config: ImageGeneration
The tool config, which image generation settings.

LocalShellCommandRequest dataclass
A request to execute a command on a shell.

Source code in src/agents/tool.py
ctx_wrapper instance-attribute

ctx_wrapper: RunContextWrapper[Any]
The run context.

data instance-attribute

data: LocalShellCall
The data from the local shell tool call.

LocalShellTool dataclass
A tool that allows the LLM to execute commands on a shell.

For more details, see: https://platform.openai.com/docs/guides/tools-local-shell

Source code in src/agents/tool.py
executor instance-attribute

executor: LocalShellExecutor
A function that executes a command on a shell.

default_tool_error_function

default_tool_error_function(
    ctx: RunContextWrapper[Any], error: Exception
) -> str
The default tool error function, which just returns a generic error message.

Source code in src/agents/tool.py
function_tool

function_tool(
    func: ToolFunction[...],
    *,
    name_override: str | None = None,
    description_override: str | None = None,
    docstring_style: DocstringStyle | None = None,
    use_docstring_info: bool = True,
    failure_error_function: ToolErrorFunction | None = None,
    strict_mode: bool = True,
    is_enabled: bool
    | Callable[
        [RunContextWrapper[Any], AgentBase],
        MaybeAwaitable[bool],
    ] = True,
) -> FunctionTool

function_tool(
    *,
    name_override: str | None = None,
    description_override: str | None = None,
    docstring_style: DocstringStyle | None = None,
    use_docstring_info: bool = True,
    failure_error_function: ToolErrorFunction | None = None,
    strict_mode: bool = True,
    is_enabled: bool
    | Callable[
        [RunContextWrapper[Any], AgentBase],
        MaybeAwaitable[bool],
    ] = True,
) -> Callable[[ToolFunction[...]], FunctionTool]

function_tool(
    func: ToolFunction[...] | None = None,
    *,
    name_override: str | None = None,
    description_override: str | None = None,
    docstring_style: DocstringStyle | None = None,
    use_docstring_info: bool = True,
    failure_error_function: ToolErrorFunction
    | None = default_tool_error_function,
    strict_mode: bool = True,
    is_enabled: bool
    | Callable[
        [RunContextWrapper[Any], AgentBase],
        MaybeAwaitable[bool],
    ] = True,
) -> (
    FunctionTool
    | Callable[[ToolFunction[...]], FunctionTool]
)
Decorator to create a FunctionTool from a function. By default, we will: 1. Parse the function signature to create a JSON schema for the tool's parameters. 2. Use the function's docstring to populate the tool's description. 3. Use the function's docstring to populate argument descriptions. The docstring style is detected automatically, but you can override it.

If the function takes a RunContextWrapper as the first argument, it must match the context type of the agent that uses the tool.

Parameters:

Name	Type	Description	Default
func	ToolFunction[...] | None	The function to wrap.	None
name_override	str | None	If provided, use this name for the tool instead of the function's name.	None
description_override	str | None	If provided, use this description for the tool instead of the function's docstring.	None
docstring_style	DocstringStyle | None	If provided, use this style for the tool's docstring. If not provided, we will attempt to auto-detect the style.	None
use_docstring_info	bool	If True, use the function's docstring to populate the tool's description and argument descriptions.	True
failure_error_function	ToolErrorFunction | None	If provided, use this function to generate an error message when the tool call fails. The error message is sent to the LLM. If you pass None, then no error message will be sent and instead an Exception will be raised.	default_tool_error_function
strict_mode	bool	Whether to enable strict mode for the tool's JSON schema. We strongly recommend setting this to True, as it increases the likelihood of correct JSON input. If False, it allows non-strict JSON schemas. For example, if a parameter has a default value, it will be optional, additional properties are allowed, etc. See here for more: https://platform.openai.com/docs/guides/structured-outputs?api-mode=responses#supported-schemas	True
is_enabled	bool | Callable[[RunContextWrapper[Any], AgentBase], MaybeAwaitable[bool]]	Whether the tool is enabled. Can be a bool or a callable that takes the run context and agent and returns whether the tool is enabled. Disabled tools are hidden from the LLM at runtime.	True
Source code in src/agents/tool.py
