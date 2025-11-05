OpenAIChatCompletionsModel
Bases: Model

Source code in src/agents/models/openai_chatcompletions.py
stream_response async

stream_response(
    system_instructions: str | None,
    input: str | list[TResponseInputItem],
    model_settings: ModelSettings,
    tools: list[Tool],
    output_schema: AgentOutputSchemaBase | None,
    handoffs: list[Handoff],
    tracing: ModelTracing,
    previous_response_id: str | None = None,
    conversation_id: str | None = None,
    prompt: ResponsePromptParam | None = None,
) -> AsyncIterator[TResponseStreamEvent]
Yields a partial message as it is generated, as well as the usage information.

Source code in src/agents/models/openai_chatcompletions.py