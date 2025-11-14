MCP Servers
MCPServer
Bases: ABC

Base class for Model Context Protocol servers.

Source code in src/agents/mcp/server.py
name abstractmethod property

name: str
A readable name for the server.

__init__

__init__(use_structured_content: bool = False)
Parameters:

Name	Type	Description	Default
use_structured_content	bool	Whether to use tool_result.structured_content when calling an MCP tool.Defaults to False for backwards compatibility - most MCP servers still include the structured content in the tool_result.content, and using it by default will cause duplicate content. You can set this to True if you know the server will not duplicate the structured content in the tool_result.content.	False
Source code in src/agents/mcp/server.py
connect abstractmethod async

connect()
Connect to the server. For example, this might mean spawning a subprocess or opening a network connection. The server is expected to remain connected until cleanup() is called.

Source code in src/agents/mcp/server.py
cleanup abstractmethod async

cleanup()
Cleanup the server. For example, this might mean closing a subprocess or closing a network connection.

Source code in src/agents/mcp/server.py
list_tools abstractmethod async

list_tools(
    run_context: RunContextWrapper[Any] | None = None,
    agent: AgentBase | None = None,
) -> list[Tool]
List the tools available on the server.

Source code in src/agents/mcp/server.py
call_tool abstractmethod async

call_tool(
    tool_name: str, arguments: dict[str, Any] | None
) -> CallToolResult
Invoke a tool on the server.

Source code in src/agents/mcp/server.py
list_prompts abstractmethod async

list_prompts() -> ListPromptsResult
List the prompts available on the server.

Source code in src/agents/mcp/server.py
get_prompt abstractmethod async

get_prompt(
    name: str, arguments: dict[str, Any] | None = None
) -> GetPromptResult
Get a specific prompt from the server.

Source code in src/agents/mcp/server.py
MCPServerStdioParams
Bases: TypedDict

Mirrors mcp.client.stdio.StdioServerParameters, but lets you pass params without another import.

Source code in src/agents/mcp/server.py
command instance-attribute

command: str
The executable to run to start the server. For example, python or node.

args instance-attribute

args: NotRequired[list[str]]
Command line args to pass to the command executable. For example, ['foo.py'] or ['server.js', '--port', '8080'].

env instance-attribute

env: NotRequired[dict[str, str]]
The environment variables to set for the server. .

cwd instance-attribute

cwd: NotRequired[str | Path]
The working directory to use when spawning the process.

encoding instance-attribute

encoding: NotRequired[str]
The text encoding used when sending/receiving messages to the server. Defaults to utf-8.

encoding_error_handler instance-attribute

encoding_error_handler: NotRequired[
    Literal["strict", "ignore", "replace"]
]
The text encoding error handler. Defaults to strict.

See https://docs.python.org/3/library/codecs.html#codec-base-classes for explanations of possible values.

MCPServerStdio
Bases: _MCPServerWithClientSession

MCP server implementation that uses the stdio transport. See the [spec] (https://spec.modelcontextprotocol.io/specification/2024-11-05/basic/transports/#stdio) for details.

Source code in src/agents/mcp/server.py
name property

name: str
A readable name for the server.

__init__

__init__(
    params: MCPServerStdioParams,
    cache_tools_list: bool = False,
    name: str | None = None,
    client_session_timeout_seconds: float | None = 5,
    tool_filter: ToolFilter = None,
    use_structured_content: bool = False,
    max_retry_attempts: int = 0,
    retry_backoff_seconds_base: float = 1.0,
)
Create a new MCP server based on the stdio transport.

Parameters:

Name	Type	Description	Default
params	MCPServerStdioParams	The params that configure the server. This includes the command to run to start the server, the args to pass to the command, the environment variables to set for the server, the working directory to use when spawning the process, and the text encoding used when sending/receiving messages to the server.	required
cache_tools_list	bool	Whether to cache the tools list. If True, the tools list will be cached and only fetched from the server once. If False, the tools list will be fetched from the server on each call to list_tools(). The cache can be invalidated by calling invalidate_tools_cache(). You should set this to True if you know the server will not change its tools list, because it can drastically improve latency (by avoiding a round-trip to the server every time).	False
name	str | None	A readable name for the server. If not provided, we'll create one from the command.	None
client_session_timeout_seconds	float | None	the read timeout passed to the MCP ClientSession.	5
tool_filter	ToolFilter	The tool filter to use for filtering tools.	None
use_structured_content	bool	Whether to use tool_result.structured_content when calling an MCP tool. Defaults to False for backwards compatibility - most MCP servers still include the structured content in the tool_result.content, and using it by default will cause duplicate content. You can set this to True if you know the server will not duplicate the structured content in the tool_result.content.	False
max_retry_attempts	int	Number of times to retry failed list_tools/call_tool calls. Defaults to no retries.	0
retry_backoff_seconds_base	float	The base delay, in seconds, for exponential backoff between retries.	1.0
Source code in src/agents/mcp/server.py
create_streams

create_streams() -> AbstractAsyncContextManager[
    tuple[
        MemoryObjectReceiveStream[
            SessionMessage | Exception
        ],
        MemoryObjectSendStream[SessionMessage],
        GetSessionIdCallback | None,
    ]
]
Create the streams for the server.

Source code in src/agents/mcp/server.py
connect async

connect()
Connect to the server.

Source code in src/agents/mcp/server.py
cleanup async

cleanup()
Cleanup the server.

Source code in src/agents/mcp/server.py
list_tools async

list_tools(
    run_context: RunContextWrapper[Any] | None = None,
    agent: AgentBase | None = None,
) -> list[Tool]
List the tools available on the server.

Source code in src/agents/mcp/server.py
call_tool async

call_tool(
    tool_name: str, arguments: dict[str, Any] | None
) -> CallToolResult
Invoke a tool on the server.

Source code in src/agents/mcp/server.py
list_prompts async

list_prompts() -> ListPromptsResult
List the prompts available on the server.

Source code in src/agents/mcp/server.py
get_prompt async

get_prompt(
    name: str, arguments: dict[str, Any] | None = None
) -> GetPromptResult
Get a specific prompt from the server.

Source code in src/agents/mcp/server.py
invalidate_tools_cache

invalidate_tools_cache()
Invalidate the tools cache.

Source code in src/agents/mcp/server.py
MCPServerSseParams
Bases: TypedDict

Mirrors the params inmcp.client.sse.sse_client.

Source code in src/agents/mcp/server.py
url instance-attribute

url: str
The URL of the server.

headers instance-attribute

headers: NotRequired[dict[str, str]]
The headers to send to the server.

timeout instance-attribute

timeout: NotRequired[float]
The timeout for the HTTP request. Defaults to 5 seconds.

sse_read_timeout instance-attribute

sse_read_timeout: NotRequired[float]
The timeout for the SSE connection, in seconds. Defaults to 5 minutes.

MCPServerSse
Bases: _MCPServerWithClientSession

MCP server implementation that uses the HTTP with SSE transport. See the [spec] (https://spec.modelcontextprotocol.io/specification/2024-11-05/basic/transports/#http-with-sse) for details.

Source code in src/agents/mcp/server.py
name property

name: str
A readable name for the server.

__init__

__init__(
    params: MCPServerSseParams,
    cache_tools_list: bool = False,
    name: str | None = None,
    client_session_timeout_seconds: float | None = 5,
    tool_filter: ToolFilter = None,
    use_structured_content: bool = False,
    max_retry_attempts: int = 0,
    retry_backoff_seconds_base: float = 1.0,
)
Create a new MCP server based on the HTTP with SSE transport.

Parameters:

Name	Type	Description	Default
params	MCPServerSseParams	The params that configure the server. This includes the URL of the server, the headers to send to the server, the timeout for the HTTP request, and the timeout for the SSE connection.	required
cache_tools_list	bool	Whether to cache the tools list. If True, the tools list will be cached and only fetched from the server once. If False, the tools list will be fetched from the server on each call to list_tools(). The cache can be invalidated by calling invalidate_tools_cache(). You should set this to True if you know the server will not change its tools list, because it can drastically improve latency (by avoiding a round-trip to the server every time).	False
name	str | None	A readable name for the server. If not provided, we'll create one from the URL.	None
client_session_timeout_seconds	float | None	the read timeout passed to the MCP ClientSession.	5
tool_filter	ToolFilter	The tool filter to use for filtering tools.	None
use_structured_content	bool	Whether to use tool_result.structured_content when calling an MCP tool. Defaults to False for backwards compatibility - most MCP servers still include the structured content in the tool_result.content, and using it by default will cause duplicate content. You can set this to True if you know the server will not duplicate the structured content in the tool_result.content.	False
max_retry_attempts	int	Number of times to retry failed list_tools/call_tool calls. Defaults to no retries.	0
retry_backoff_seconds_base	float	The base delay, in seconds, for exponential backoff between retries.	1.0
Source code in src/agents/mcp/server.py
create_streams

create_streams() -> AbstractAsyncContextManager[
    tuple[
        MemoryObjectReceiveStream[
            SessionMessage | Exception
        ],
        MemoryObjectSendStream[SessionMessage],
        GetSessionIdCallback | None,
    ]
]
Create the streams for the server.

Source code in src/agents/mcp/server.py
connect async

connect()
Connect to the server.

Source code in src/agents/mcp/server.py
cleanup async

cleanup()
Cleanup the server.

Source code in src/agents/mcp/server.py
list_tools async

list_tools(
    run_context: RunContextWrapper[Any] | None = None,
    agent: AgentBase | None = None,
) -> list[Tool]
List the tools available on the server.

Source code in src/agents/mcp/server.py
call_tool async

call_tool(
    tool_name: str, arguments: dict[str, Any] | None
) -> CallToolResult
Invoke a tool on the server.

Source code in src/agents/mcp/server.py
list_prompts async

list_prompts() -> ListPromptsResult
List the prompts available on the server.

Source code in src/agents/mcp/server.py
get_prompt async

get_prompt(
    name: str, arguments: dict[str, Any] | None = None
) -> GetPromptResult
Get a specific prompt from the server.

Source code in src/agents/mcp/server.py
invalidate_tools_cache

invalidate_tools_cache()
Invalidate the tools cache.

Source code in src/agents/mcp/server.py
MCPServerStreamableHttpParams
Bases: TypedDict

Mirrors the params inmcp.client.streamable_http.streamablehttp_client.

Source code in src/agents/mcp/server.py
url instance-attribute

url: str
The URL of the server.

headers instance-attribute

headers: NotRequired[dict[str, str]]
The headers to send to the server.

timeout instance-attribute

timeout: NotRequired[timedelta | float]
The timeout for the HTTP request. Defaults to 5 seconds.

sse_read_timeout instance-attribute

sse_read_timeout: NotRequired[timedelta | float]
The timeout for the SSE connection, in seconds. Defaults to 5 minutes.

terminate_on_close instance-attribute

terminate_on_close: NotRequired[bool]
Terminate on close

MCPServerStreamableHttp
Bases: _MCPServerWithClientSession

MCP server implementation that uses the Streamable HTTP transport. See the [spec] (https://modelcontextprotocol.io/specification/2025-03-26/basic/transports#streamable-http) for details.

Source code in src/agents/mcp/server.py
name property

name: str
A readable name for the server.

__init__

__init__(
    params: MCPServerStreamableHttpParams,
    cache_tools_list: bool = False,
    name: str | None = None,
    client_session_timeout_seconds: float | None = 5,
    tool_filter: ToolFilter = None,
    use_structured_content: bool = False,
    max_retry_attempts: int = 0,
    retry_backoff_seconds_base: float = 1.0,
)
Create a new MCP server based on the Streamable HTTP transport.

Parameters:

Name	Type	Description	Default
params	MCPServerStreamableHttpParams	The params that configure the server. This includes the URL of the server, the headers to send to the server, the timeout for the HTTP request, and the timeout for the Streamable HTTP connection and whether we need to terminate on close.	required
cache_tools_list	bool	Whether to cache the tools list. If True, the tools list will be cached and only fetched from the server once. If False, the tools list will be fetched from the server on each call to list_tools(). The cache can be invalidated by calling invalidate_tools_cache(). You should set this to True if you know the server will not change its tools list, because it can drastically improve latency (by avoiding a round-trip to the server every time).	False
name	str | None	A readable name for the server. If not provided, we'll create one from the URL.	None
client_session_timeout_seconds	float | None	the read timeout passed to the MCP ClientSession.	5
tool_filter	ToolFilter	The tool filter to use for filtering tools.	None
use_structured_content	bool	Whether to use tool_result.structured_content when calling an MCP tool. Defaults to False for backwards compatibility - most MCP servers still include the structured content in the tool_result.content, and using it by default will cause duplicate content. You can set this to True if you know the server will not duplicate the structured content in the tool_result.content.	False
max_retry_attempts	int	Number of times to retry failed list_tools/call_tool calls. Defaults to no retries.	0
retry_backoff_seconds_base	float	The base delay, in seconds, for exponential backoff between retries.	1.0
Source code in src/agents/mcp/server.py
create_streams

create_streams() -> AbstractAsyncContextManager[
    tuple[
        MemoryObjectReceiveStream[
            SessionMessage | Exception
        ],
        MemoryObjectSendStream[SessionMessage],
        GetSessionIdCallback | None,
    ]
]
Create the streams for the server.

Source code in src/agents/mcp/server.py
connect async

connect()
Connect to the server.

Source code in src/agents/mcp/server.py
cleanup async

cleanup()
Cleanup the server.

Source code in src/agents/mcp/server.py
list_tools async

list_tools(
    run_context: RunContextWrapper[Any] | None = None,
    agent: AgentBase | None = None,
) -> list[Tool]
List the tools available on the server.

Source code in src/agents/mcp/server.py
call_tool async

call_tool(
    tool_name: str, arguments: dict[str, Any] | None
) -> CallToolResult
Invoke a tool on the server.

Source code in src/agents/mcp/server.py
list_prompts async

list_prompts() -> ListPromptsResult
List the prompts available on the server.

Source code in src/agents/mcp/server.py
get_prompt async

get_prompt(
    name: str, arguments: dict[str, Any] | None = None
) -> GetPromptResult
Get a specific prompt from the server.

Source code in src/agents/mcp/server.py
invalidate_tools_cache

invalidate_tools_cache()
Invalidate the tools cache.

Source code in src/agents/mcp/server.py
