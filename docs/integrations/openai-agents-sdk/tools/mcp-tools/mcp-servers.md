## `MCPServer`
**Bases:** `ABC`

Base class for Model Context Protocol servers.

[Source code in src/agents/mcp/server.py](src/agents/mcp/server.py)

---

### `name`
<sup>*abstractmethod property*</sup>

```python
name: str
```
A readable name for the server.

---

### `__init__`

```python
__init__(use_structured_content: bool = False)
```

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `use_structured_content` | `bool` | Whether to use `tool_result.structured_content` when calling an MCP tool. Defaults to `False` for backwards compatibility - most MCP servers still include the structured content in the `tool_result.content`, and using it by default will cause duplicate content. You can set this to `True` if you know the server will not duplicate the structured content in the `tool_result.content`. | `False` |

[Source code in src/agents/mcp/server.py](src/agents/mcp/server.py)

---

### `connect`
<sup>*abstractmethod async*</sup>

```python
connect()
```
Connect to the server. For example, this might mean spawning a subprocess or opening a network connection. The server is expected to remain connected until `cleanup()` is called.

[Source code in src/agents/mcp/server.py](src/agents/mcp/server.py)

---

### `cleanup`
<sup>*abstractmethod async*</sup>

```python
cleanup()
```
Cleanup the server. For example, this might mean closing a subprocess or closing a network connection.

[Source code in src/agents/mcp/server.py](src/agents/mcp/server.py)

---

### `list_tools`
<sup>*abstractmethod async*</sup>

```python
list_tools(
    run_context: RunContextWrapper[Any] | None = None,
    agent: AgentBase | None = None,
) -> list[Tool]
```
List the tools available on the server.

[Source code in src/agents/mcp/server.py](src/agents/mcp/server.py)

---

### `call_tool`
<sup>*abstractmethod async*</sup>

```python
call_tool(
    tool_name: str, 
    arguments: dict[str, Any] | None
) -> CallToolResult
```
Invoke a tool on the server.

[Source code in src/agents/mcp/server.py](src/agents/mcp/server.py)

---

### `list_prompts`
<sup>*abstractmethod async*</sup>

```python
list_prompts() -> ListPromptsResult
```
List the prompts available on the server.

[Source code in src/agents/mcp/server.py](src/agents/mcp/server.py)

---

### `get_prompt`
<sup>*abstractmethod async*</sup>

```python
get_prompt(
    name: str, 
    arguments: dict[str, Any] | None = None
) -> GetPromptResult
```
Get a specific prompt from the server.

[Source code in src/agents/mcp/server.py](src/agents/mcp/server.py)

---
---

## `MCPServerStdioParams`
**Bases:** `TypedDict`

Mirrors `mcp.client.stdio.StdioServerParameters`, but lets you pass params without another import.

[Source code in src/agents/mcp/server.py](src/agents/mcp/server.py)

### `command`
<sup>*instance-attribute*</sup>
```python
command: str
```
The executable to run to start the server. For example, `python` or `node`.

### `args`
<sup>*instance-attribute*</sup>
```python
args: NotRequired[list[str]]
```
Command line args to pass to the command executable. For example, `['foo.py']` or `['server.js', '--port', '8080']`.

### `env`
<sup>*instance-attribute*</sup>
```python
env: NotRequired[dict[str, str]]
```
The environment variables to set for the server.

### `cwd`
<sup>*instance-attribute*</sup>
```python
cwd: NotRequired[str | Path]
```
The working directory to use when spawning the process.

### `encoding`
<sup>*instance-attribute*</sup>
```python
encoding: NotRequired[str]
```
The text encoding used when sending/receiving messages to the server. Defaults to `utf-8`.

### `encoding_error_handler`
<sup>*instance-attribute*</sup>
```python
encoding_error_handler: NotRequired[
    Literal["strict", "ignore", "replace"]
]
```
The text encoding error handler. Defaults to `strict`.

See [https://docs.python.org/3/library/codecs.html#codec-base-classes](https://docs.python.org/3/library/codecs.html#codec-base-classes) for explanations of possible values.

---
---

## `MCPServerStdio`
**Bases:** `_MCPServerWithClientSession`

MCP server implementation that uses the stdio transport. See the [spec](https://spec.modelcontextprotocol.io/specification/2024-11-05/basic/transports/#stdio) for details.

[Source code in src/agents/mcp/server.py](src/agents/mcp/server.py)

---

### `name`
<sup>*property*</sup>
```python
name: str
```
A readable name for the server.

---

### `__init__`

```python
__init__(
    params: MCPServerStdioParams,
    cache_tools_list: bool = False,
    name: str | None = None,
    client_session_timeout_seconds: float | None = 5,
    tool_filter: ToolFilter = None,
    use_structured_content: bool = False,
    max_retry_attempts: int = 0,
    retry_backoff_seconds_base: float = 1.0,
    message_handler: MessageHandlerFnT | None = None,
)
```
Create a new MCP server based on the stdio transport.

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `params` | `MCPServerStdioParams` | The params that configure the server. This includes the command to run to start the server, the args to pass to the command, the environment variables to set for the server, the working directory to use when spawning the process, and the text encoding used when sending/receiving messages to the server. | *required* |
| `cache_tools_list` | `bool` | Whether to cache the tools list. If `True`, the tools list will be cached and only fetched from the server once. If `False`, the tools list will be fetched from the server on each call to `list_tools()`. The cache can be invalidated by calling `invalidate_tools_cache()`. You should set this to `True` if you know the server will not change its tools list, because it can drastically improve latency (by avoiding a round-trip to the server every time). | `False` |
| `name` | `str | None` | A readable name for the server. If not provided, we'll create one from the command. | `None` |
| `client_session_timeout_seconds` | `float | None` | The read timeout passed to the MCP `ClientSession`. | `5` |
| `tool_filter` | `ToolFilter` | The tool filter to use for filtering tools. | `None` |
| `use_structured_content` | `bool` | Whether to use `tool_result.structured_content` when calling an MCP tool. Defaults to `False` for backwards compatibility - most MCP servers still include the structured content in the `tool_result.content`, and using it by default will cause duplicate content. You can set this to `True` if you know the server will not duplicate the structured content in the `tool_result.content`. | `False` |
| `max_retry_attempts` | `int` | Number of times to retry failed `list_tools`/`call_tool` calls. Defaults to no retries. | `0` |
| `retry_backoff_seconds_base` | `float` | The base delay, in seconds, for exponential backoff between retries. | `1.0` |
| `message_handler` | `MessageHandlerFnT | None` | Optional handler invoked for session messages as delivered by the `ClientSession`. | `None` |

[Source code in src/agents/mcp/server.py](src/agents/mcp/server.py)

---

### `create_streams`

```python
create_streams() -> AbstractAsyncContextManager[
    tuple[
        MemoryObjectReceiveStream[
            SessionMessage | Exception
        ],
        MemoryObjectSendStream[SessionMessage],
        GetSessionIdCallback | None,
    ]
]
```
Create the streams for the server.

[Source code in src/agents/mcp/server.py](src/agents/mcp/server.py)

---

### `connect`
<sup>*async*</sup>

```python
connect()
```
Connect to the server.

[Source code in src/agents/mcp/server.py](src/agents/mcp/server.py)

---

### `cleanup`
<sup>*async*</sup>

```python
cleanup()
```
Cleanup the server.

[Source code in src/agents/mcp/server.py](src/agents/mcp/server.py)

---

### `list_tools`
<sup>*async*</sup>

```python
list_tools(
    run_context: RunContextWrapper[Any] | None = None,
    agent: AgentBase | None = None,
) -> list[Tool]
```
List the tools available on the server.

[Source code in src/agents/mcp/server.py](src/agents/mcp/server.py)

---

### `call_tool`
<sup>*async*</sup>

```python
call_tool(
    tool_name: str, 
    arguments: dict[str, Any] | None
) -> CallToolResult
```
Invoke a tool on the server.

[Source code in src/agents/mcp/server.py](src/agents/mcp/server.py)

---

### `list_prompts`
<sup>*async*</sup>

```python
list_prompts() -> ListPromptsResult
```
List the prompts available on the server.

[Source code in src/agents/mcp/server.py](src/agents/mcp/server.py)

---

### `get_prompt`
<sup>*async*</sup>

```python
get_prompt(
    name: str, 
    arguments: dict[str, Any] | None = None
) -> GetPromptResult
```
Get a specific prompt from the server.

[Source code in src/agents/mcp/server.py](src/agents/mcp/server.py)

---

### `invalidate_tools_cache`

```python
invalidate_tools_cache()
```
Invalidate the tools cache.

[Source code in src/agents/mcp/server.py](src/agents/mcp/server.py)

---
---

## `MCPServerSseParams`
**Bases:** `TypedDict`

Mirrors the params in `mcp.client.sse.sse_client`.

[Source code in src/agents/mcp/server.py](src/agents/mcp/server.py)

### `url`
<sup>*instance-attribute*</sup>
```python
url: str
```
The URL of the server.

### `headers`
<sup>*instance-attribute*</sup>
```python
headers: NotRequired[dict[str, str]]
```
The headers to send to the server.

### `timeout`
<sup>*instance-attribute*</sup>
```python
timeout: NotRequired[float]
```
The timeout for the HTTP request. Defaults to 5 seconds.

### `sse_read_timeout`
<sup>*instance-attribute*</sup>
```python
sse_read_timeout: NotRequired[float]
```
The timeout for the SSE connection, in seconds. Defaults to 5 minutes.

---
---

## `MCPServerSse`
**Bases:** `_MCPServerWithClientSession`

MCP server implementation that uses the HTTP with SSE transport. See the [spec](https://spec.modelcontextprotocol.io/specification/2024-11-05/basic/transports/#http-with-sse) for details.

[Source code in src/agents/mcp/server.py](src/agents/mcp/server.py)

---

### `name`
<sup>*property*</sup>
```python
name: str
```
A readable name for the server.

---

### `__init__`

```python
__init__(
    params: MCPServerSseParams,
    cache_tools_list: bool = False,
    name: str | None = None,
    client_session_timeout_seconds: float | None = 5,
    tool_filter: ToolFilter = None,
    use_structured_content: bool = False,
    max_retry_attempts: int = 0,
    retry_backoff_seconds_base: float = 1.0,
    message_handler: MessageHandlerFnT | None = None,
)
```
Create a new MCP server based on the HTTP with SSE transport.

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `params` | `MCPServerSseParams` | The params that configure the server. This includes the URL of the server, the headers to send to the server, the timeout for the HTTP request, and the timeout for the SSE connection. | *required* |
| `cache_tools_list` | `bool` | Whether to cache the tools list. If `True`, the tools list will be cached and only fetched from the server once. If `False`, the tools list will be fetched from the server on each call to `list_tools()`. The cache can be invalidated by calling `invalidate_tools_cache()`. You should set this to `True` if you know the server will not change its tools list, because it can drastically improve latency (by avoiding a round-trip to the server every time). | `False` |
| `name` | `str | None` | A readable name for the server. If not provided, we'll create one from the URL. | `None` |
| `client_session_timeout_seconds` | `float | None` | The read timeout passed to the MCP `ClientSession`. | `5` |
| `tool_filter` | `ToolFilter` | The tool filter to use for filtering tools. | `None` |
| `use_structured_content` | `bool` | Whether to use `tool_result.structured_content` when calling an MCP tool. Defaults to `False` for backwards compatibility - most MCP servers still include the structured content in the `tool_result.content`, and using it by default will cause duplicate content. You can set this to `True` if you know the server will not duplicate the structured content in the `tool_result.content`. | `False` |
| `max_retry_attempts` | `int` | Number of times to retry failed `list_tools`/`call_tool` calls. Defaults to no retries. | `0` |
| `retry_backoff_seconds_base` | `float` | The base delay, in seconds, for exponential backoff between retries. | `1.0` |
| `message_handler` | `MessageHandlerFnT | None` | Optional handler invoked for session messages as delivered by the `ClientSession`. | `None` |

[Source code in src/agents/mcp/server.py](src/agents/mcp/server.py)

---

### `create_streams`

```python
create_streams() -> AbstractAsyncContextManager[
    tuple[
        MemoryObjectReceiveStream[
            SessionMessage | Exception
        ],
        MemoryObjectSendStream[SessionMessage],
        GetSessionIdCallback | None,
    ]
]
```
Create the streams for the server.

[Source code in src/agents/mcp/server.py](src/agents/mcp/server.py)

---

### `connect`
<sup>*async*</sup>

```python
connect()
```
Connect to the server.

[Source code in src/agents/mcp/server.py](src/agents/mcp/server.py)

---

### `cleanup`
<sup>*async*</sup>

```python
cleanup()
```
Cleanup the server.

[Source code in src/agents/mcp/server.py](src/agents/mcp/server.py)

---

### `list_tools`
<sup>*async*</sup>

```python
list_tools(
    run_context: RunContextWrapper[Any] | None = None,
    agent: AgentBase | None = None,
) -> list[Tool]
```
List the tools available on the server.

[Source code in src/agents/mcp/server.py](src/agents/mcp/server.py)

---

### `call_tool`
<sup>*async*</sup>

```python
call_tool(
    tool_name: str, 
    arguments: dict[str, Any] | None
) -> CallToolResult
```
Invoke a tool on the server.

[Source code in src/agents/mcp/server.py](src/agents/mcp/server.py)

---

### `list_prompts`
<sup>*async*</sup>

```python
list_prompts() -> ListPromptsResult
```
List the prompts available on the server.

[Source code in src/agents/mcp/server.py](src/agents/mcp/server.py)

---

### `get_prompt`
<sup>*async*</sup>

```python
get_prompt(
    name: str, 
    arguments: dict[str, Any] | None = None
) -> GetPromptResult
```
Get a specific prompt from the server.

[Source code in src/agents/mcp/server.py](src/agents/mcp/server.py)

---

### `invalidate_tools_cache`

```python
invalidate_tools_cache()
```
Invalidate the tools cache.

[Source code in src/agents/mcp/server.py](src/agents/mcp/server.py)

---
---

## `MCPServerStreamableHttpParams`
**Bases:** `TypedDict`

Mirrors the params in `mcp.client.streamable_http.streamablehttp_client`.

[Source code in src/agents/mcp/server.py](src/agents/mcp/server.py)

### `url`
<sup>*instance-attribute*</sup>
```python
url: str
```
The URL of the server.

### `headers`
<sup>*instance-attribute*</sup>
```python
headers: NotRequired[dict[str, str]]
```
The headers to send to the server.

### `timeout`
<sup>*instance-attribute*</sup>
```python
timeout: NotRequired[timedelta | float]
```
The timeout for the HTTP request. Defaults to 5 seconds.

### `sse_read_timeout`
<sup>*instance-attribute*</sup>
```python
sse_read_timeout: NotRequired[timedelta | float]
```
The timeout for the SSE connection, in seconds. Defaults to 5 minutes.

### `terminate_on_close`
<sup>*instance-attribute*</sup>
```python
terminate_on_close: NotRequired[bool]
```
Terminate on close.

### `httpx_client_factory`
<sup>*instance-attribute*</sup>
```python
httpx_client_factory: NotRequired[HttpClientFactory]
```
Custom HTTP client factory for configuring `httpx.AsyncClient` behavior.

---
---

## `MCPServerStreamableHttp`
**Bases:** `_MCPServerWithClientSession`

MCP server implementation that uses the Streamable HTTP transport. See the [spec](https://modelcontextprotocol.io/specification/2025-03-26/basic/transports#streamable-http) for details.

[Source code in src/agents/mcp/server.py](src/agents/mcp/server.py)

---

### `name`
<sup>*property*</sup>
```python
name: str
```
A readable name for the server.

---

### `__init__`

```python
__init__(
    params: MCPServerStreamableHttpParams,
    cache_tools_list: bool = False,
    name: str | None = None,
    client_session_timeout_seconds: float | None = 5,
    tool_filter: ToolFilter = None,
    use_structured_content: bool = False,
    max_retry_attempts: int = 0,
    retry_backoff_seconds_base: float = 1.0,
    message_handler: MessageHandlerFnT | None = None,
)
```
Create a new MCP server based on the Streamable HTTP transport.

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `params` | `MCPServerStreamableHttpParams` | The params that configure the server. This includes the URL of the server, the headers to send to the server, the timeout for the HTTP request, the timeout for the Streamable HTTP connection, whether we need to terminate on close, and an optional custom HTTP client factory. | *required* |
| `cache_tools_list` | `bool` | Whether to cache the tools list. If `True`, the tools list will be cached and only fetched from the server once. If `False`, the tools list will be fetched from the server on each call to `list_tools()`. The cache can be invalidated by calling `invalidate_tools_cache()`. You should set this to `True` if you know the server will not change its tools list, because it can drastically improve latency (by avoiding a round-trip to the server every time). | `False` |
| `name` | `str | None` | A readable name for the server. If not provided, we'll create one from the URL. | `None` |
| `client_session_timeout_seconds` | `float | None` | The read timeout passed to the MCP `ClientSession`. | `5` |
| `tool_filter` | `ToolFilter` | The tool filter to use for filtering tools. | `None` |
| `use_structured_content` | `bool` | Whether to use `tool_result.structured_content` when calling an MCP tool. Defaults to `False` for backwards compatibility - most MCP servers still include the structured content in the `tool_result.content`, and using it by default will cause duplicate content. You can set this to `True` if you know the server will not duplicate the structured content in the `tool_result.content`. | `False` |
| `max_retry_attempts` | `int` | Number of times to retry failed `list_tools`/`call_tool` calls. Defaults to no retries. | `0` |
| `retry_backoff_seconds_base` | `float` | The base delay, in seconds, for exponential backoff between retries. | `1.0` |
| `message_handler` | `MessageHandlerFnT | None` | Optional handler invoked for session messages as delivered by the `ClientSession`. | `None` |

[Source code in src/agents/mcp/server.py](src/agents/mcp/server.py)

---

### `create_streams`

```python
create_streams() -> AbstractAsyncContextManager[
    tuple[
        MemoryObjectReceiveStream[
            SessionMessage | Exception
        ],
        MemoryObjectSendStream[SessionMessage],
        GetSessionIdCallback | None,
    ]
]
```
Create the streams for the server.

[Source code in src/agents/mcp/server.py](src/agents/mcp/server.py)

---

### `connect`
<sup>*async*</sup>

```python
connect()
```
Connect to the server.

[Source code in src/agents/mcp/server.py](src/agents/mcp/server.py)

---

### `cleanup`
<sup>*async*</sup>

```python
cleanup()
```
Cleanup the server.

[Source code in src/agents/mcp/server.py](src/agents/mcp/server.py)

---

### `list_tools`
<sup>*async*</sup>

```python
list_tools(
    run_context: RunContextWrapper[Any] | None = None,
    agent: AgentBase | None = None,
) -> list[Tool]
```
List the tools available on the server.

[Source code in src/agents/mcp/server.py](src/agents/mcp/server.py)

---

### `call_tool`
<sup>*async*</sup>

```python
call_tool(
    tool_name: str, 
    arguments: dict[str, Any] | None
) -> CallToolResult
```
Invoke a tool on the server.

[Source code in src/agents/mcp/server.py](src/agents/mcp/server.py)

---

### `list_prompts`
<sup>*async*</sup>

```python
list_prompts() -> ListPromptsResult
```
List the prompts available on the server.

[Source code in src/agents/mcp/server.py](src/agents/mcp/server.py)

---

### `get_prompt`
<sup>*async*</sup>

```python
get_prompt(
    name: str, 
    arguments: dict[str, Any] | None = None
) -> GetPromptResult
```
Get a specific prompt from the server.

[Source code in src/agents/mcp/server.py](src/agents/mcp/server.py)

---

### `invalidate_tools_cache`

```python
invalidate_tools_cache()
```
Invalidate the tools cache.

[Source code in src/agents/mcp/server.py](src/agents/mcp/server.py)