Agents module
set_default_openai_key

set_default_openai_key(
    key: str, use_for_tracing: bool = True
) -> None
Set the default OpenAI API key to use for LLM requests (and optionally tracing(). This is only necessary if the OPENAI_API_KEY environment variable is not already set.

If provided, this key will be used instead of the OPENAI_API_KEY environment variable.

Parameters:

Name	Type	Description	Default
key	str	The OpenAI key to use.	required
use_for_tracing	bool	Whether to also use this key to send traces to OpenAI. Defaults to True If False, you'll either need to set the OPENAI_API_KEY environment variable or call set_tracing_export_api_key() with the API key you want to use for tracing.	True
Source code in src/agents/__init__.py
set_default_openai_client

set_default_openai_client(
    client: AsyncOpenAI, use_for_tracing: bool = True
) -> None
Set the default OpenAI client to use for LLM requests and/or tracing. If provided, this client will be used instead of the default OpenAI client.

Parameters:

Name	Type	Description	Default
client	AsyncOpenAI	The OpenAI client to use.	required
use_for_tracing	bool	Whether to use the API key from this client for uploading traces. If False, you'll either need to set the OPENAI_API_KEY environment variable or call set_tracing_export_api_key() with the API key you want to use for tracing.	True
Source code in src/agents/__init__.py
set_default_openai_api

set_default_openai_api(
    api: Literal["chat_completions", "responses"],
) -> None
Set the default API to use for OpenAI LLM requests. By default, we will use the responses API but you can set this to use the chat completions API instead.

Source code in src/agents/__init__.py
set_tracing_export_api_key

set_tracing_export_api_key(api_key: str) -> None
Set the OpenAI API key for the backend exporter.

Source code in src/agents/tracing/__init__.py
set_tracing_disabled

set_tracing_disabled(disabled: bool) -> None
Set whether tracing is globally disabled.

Source code in src/agents/tracing/__init__.py
set_trace_processors

set_trace_processors(
    processors: list[TracingProcessor],
) -> None
Set the list of trace processors. This will replace the current list of processors.

Source code in src/agents/tracing/__init__.py
enable_verbose_stdout_logging

enable_verbose_stdout_logging()
Enables verbose logging to stdout. This is useful for debugging.

Source code in src/agents/__init__.py