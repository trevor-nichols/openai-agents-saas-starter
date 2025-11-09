.
├── examples/                  # Contains usage examples and documentation for the SDK.
│   └── tools.md               # Explains and demonstrates how to use different types of tools.
├── raw-outputs/               # Contains raw log files from streaming API calls for testing or debugging.
│   ├── combined-streaming/    # Logs for streams combining multiple tool types (e.g., web search and functions).
│   │   └── stream-log-2025-11-07T00-28-16.md # A raw log of a combined web search and function call stream.
│   ├── function-streaming/    # Logs specifically for function calling streams.
│   │   └── stream-log-2025-11-07T00-22-38.md # A raw log of a function calling stream.
│   └── structured-streaming/  # Logs for streams that generate structured JSON output.
│       ├── stream-log-2025-11-07T17-03-24.md # A raw log of a structured JSON output stream.
│       └── stream-log-2025-11-07T17-32-51.md # Another raw log of a structured JSON output stream.
├── tool_context.md            # API documentation for the `ToolContext` dataclass.
└── tools.md                   # API documentation for various tool classes and the `function_tool` decorator.