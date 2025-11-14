Model settings
ModelSettings
Settings to use when calling an LLM.

This class holds optional model configuration parameters (e.g. temperature, top_p, penalties, truncation, etc.).

Not all models/providers support all of these parameters, so please check the API documentation for the specific model and provider you are using.

Source code in src/agents/model_settings.py
temperature class-attribute instance-attribute

temperature: float | None = None
The temperature to use when calling the model.

top_p class-attribute instance-attribute

top_p: float | None = None
The top_p to use when calling the model.

frequency_penalty class-attribute instance-attribute

frequency_penalty: float | None = None
The frequency penalty to use when calling the model.

presence_penalty class-attribute instance-attribute

presence_penalty: float | None = None
The presence penalty to use when calling the model.

tool_choice class-attribute instance-attribute

tool_choice: ToolChoice | None = None
The tool choice to use when calling the model.

parallel_tool_calls class-attribute instance-attribute

parallel_tool_calls: bool | None = None
Controls whether the model can make multiple parallel tool calls in a single turn. If not provided (i.e., set to None), this behavior defers to the underlying model provider's default. For most current providers (e.g., OpenAI), this typically means parallel tool calls are enabled (True). Set to True to explicitly enable parallel tool calls, or False to restrict the model to at most one tool call per turn.

truncation class-attribute instance-attribute

truncation: Literal['auto', 'disabled'] | None = None
The truncation strategy to use when calling the model. See Responses API documentation for more details.

max_tokens class-attribute instance-attribute

max_tokens: int | None = None
The maximum number of output tokens to generate.

reasoning class-attribute instance-attribute

reasoning: Reasoning | None = None
Configuration options for reasoning models.

verbosity class-attribute instance-attribute

verbosity: Literal['low', 'medium', 'high'] | None = None
Constrains the verbosity of the model's response.

metadata class-attribute instance-attribute

metadata: dict[str, str] | None = None
Metadata to include with the model response call.

store class-attribute instance-attribute

store: bool | None = None
Whether to store the generated model response for later retrieval. For Responses API: automatically enabled when not specified. For Chat Completions API: disabled when not specified.

include_usage class-attribute instance-attribute

include_usage: bool | None = None
Whether to include usage chunk. Only available for Chat Completions API.

response_include class-attribute instance-attribute

response_include: list[ResponseIncludable | str] | None = (
    None
)
Additional output data to include in the model response. include parameter

top_logprobs class-attribute instance-attribute

top_logprobs: int | None = None
Number of top tokens to return logprobs for. Setting this will automatically include "message.output_text.logprobs" in the response.

extra_query class-attribute instance-attribute

extra_query: Query | None = None
Additional query fields to provide with the request. Defaults to None if not provided.

extra_body class-attribute instance-attribute

extra_body: Body | None = None
Additional body fields to provide with the request. Defaults to None if not provided.

extra_headers class-attribute instance-attribute

extra_headers: Headers | None = None
Additional headers to provide with the request. Defaults to None if not provided.

extra_args class-attribute instance-attribute

extra_args: dict[str, Any] | None = None
Arbitrary keyword arguments to pass to the model API call. These will be passed directly to the underlying model provider's API. Use with caution as not all models support all parameters.

resolve

resolve(override: ModelSettings | None) -> ModelSettings
Produce a new ModelSettings by overlaying any non-None values from the override on top of this instance.

Source code in src/agents/model_settings.py
