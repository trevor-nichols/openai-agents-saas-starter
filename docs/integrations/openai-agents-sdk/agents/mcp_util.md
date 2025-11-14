MCP Util
ToolFilterCallable module-attribute

ToolFilterCallable = Callable[
    ["ToolFilterContext", "MCPTool"], MaybeAwaitable[bool]
]
A function that determines whether a tool should be available.

Parameters:

Name	Type	Description	Default
context		The context information including run context, agent, and server name.	required
tool		The MCP tool to filter.	required
Returns:

Type	Description
Whether the tool should be available (True) or filtered out (False).
ToolFilter module-attribute

ToolFilter = Union[
    ToolFilterCallable, ToolFilterStatic, None
]
A tool filter that can be either a function, static configuration, or None (no filtering).

ToolFilterContext dataclass
Context information available to tool filter functions.

Source code in src/agents/mcp/util.py
run_context instance-attribute

run_context: RunContextWrapper[Any]
The current run context.

agent instance-attribute

agent: AgentBase
The agent that is requesting the tool list.

server_name instance-attribute

server_name: str
The name of the MCP server.

ToolFilterStatic
Bases: TypedDict

Static tool filter configuration using allowlists and blocklists.

Source code in src/agents/mcp/util.py
allowed_tool_names instance-attribute

allowed_tool_names: NotRequired[list[str]]
Optional list of tool names to allow (whitelist). If set, only these tools will be available.

blocked_tool_names instance-attribute

blocked_tool_names: NotRequired[list[str]]
Optional list of tool names to exclude (blacklist). If set, these tools will be filtered out.

MCPUtil
Set of utilities for interop between MCP and Agents SDK tools.

Source code in src/agents/mcp/util.py
get_all_function_tools async classmethod

get_all_function_tools(
    servers: list[MCPServer],
    convert_schemas_to_strict: bool,
    run_context: RunContextWrapper[Any],
    agent: AgentBase,
) -> list[Tool]
Get all function tools from a list of MCP servers.

Source code in src/agents/mcp/util.py
get_function_tools async classmethod

get_function_tools(
    server: MCPServer,
    convert_schemas_to_strict: bool,
    run_context: RunContextWrapper[Any],
    agent: AgentBase,
) -> list[Tool]
Get all function tools from a single MCP server.

Source code in src/agents/mcp/util.py
to_function_tool classmethod

to_function_tool(
    tool: Tool,
    server: MCPServer,
    convert_schemas_to_strict: bool,
) -> FunctionTool
Convert an MCP tool to an Agents SDK function tool.

Source code in src/agents/mcp/util.py
invoke_mcp_tool async classmethod

invoke_mcp_tool(
    server: MCPServer,
    tool: Tool,
    context: RunContextWrapper[Any],
    input_json: str,
) -> str
Invoke an MCP tool and return the result as a string.

Source code in src/agents/mcp/util.py
create_static_tool_filter

create_static_tool_filter(
    allowed_tool_names: Optional[list[str]] = None,
    blocked_tool_names: Optional[list[str]] = None,
) -> Optional[ToolFilterStatic]
Create a static tool filter from allowlist and blocklist parameters.

This is a convenience function for creating a ToolFilterStatic.

Parameters:

Name	Type	Description	Default
allowed_tool_names	Optional[list[str]]	Optional list of tool names to allow (whitelist).	None
blocked_tool_names	Optional[list[str]]	Optional list of tool names to exclude (blacklist).	None
Returns:

Type	Description
Optional[ToolFilterStatic]	A ToolFilterStatic if any filtering is specified, None otherwise.
Source code in src/agents/mcp/util.py
