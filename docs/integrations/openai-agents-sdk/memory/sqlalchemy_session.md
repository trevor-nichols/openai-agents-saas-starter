# SQLAlchemy Sessions

`SQLAlchemySession` uses SQLAlchemy to provide a production-ready session implementation, allowing you to use any database supported by SQLAlchemy (PostgreSQL, MySQL, SQLite, etc.) for session storage.

## Installation

SQLAlchemy sessions require the `sqlalchemy` extra:

```bash
pip install openai-agents[sqlalchemy]
```

## Quick start

### Using database URL

The simplest way to get started:

```python
import asyncio
from agents import Agent, Runner
from agents.extensions.memory import SQLAlchemySession

async def main():
    agent = Agent("Assistant")

    # Create session using database URL
    session = SQLAlchemySession.from_url(
        "user-123",
        url="sqlite+aiosqlite:///:memory:",
        create_tables=True
    )

    result = await Runner.run(agent, "Hello", session=session)
    print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())
```

### Using existing engine

For applications with existing SQLAlchemy engines:

```python
import asyncio
from agents import Agent, Runner
from agents.extensions.memory import SQLAlchemySession
from sqlalchemy.ext.asyncio import create_async_engine

async def main():
    # Create your database engine
    engine = create_async_engine("postgresql+asyncpg://user:pass@localhost/db")

    agent = Agent("Assistant")
    session = SQLAlchemySession(
        "user-456",
        engine=engine,
        create_tables=True
    )

    result = await Runner.run(agent, "Hello", session=session)
    print(result.final_output)

    # Clean up
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
```

## API Reference

*   `SQLAlchemySession` - Main class
*   `Session` - Base session protocol

---

# Advanced SQLite Sessions

`AdvancedSQLiteSession` is an enhanced version of the basic `SQLiteSession` that provides advanced conversation management capabilities including conversation branching, detailed usage analytics, and structured conversation queries.

## Features

*   **Conversation branching:** Create alternative conversation paths from any user message
*   **Usage tracking:** Detailed token usage analytics per turn with full JSON breakdowns
*   **Structured queries:** Get conversations by turns, tool usage statistics, and more
*   **Branch management:** Independent branch switching and management
*   **Message structure metadata:** Track message types, tool usage, and conversation flow

## Quick start

```python
from agents import Agent, Runner
from agents.extensions.memory import AdvancedSQLiteSession

# Create agent
agent = Agent(
    name="Assistant",
    instructions="Reply very concisely.",
)

# Create an advanced session
session = AdvancedSQLiteSession(
    session_id="conversation_123",
    db_path="conversations.db",
    create_tables=True
)

# First conversation turn
result = await Runner.run(
    agent,
    "What city is the Golden Gate Bridge in?",
    session=session
)
print(result.final_output)  # "San Francisco"

# IMPORTANT: Store usage data
await session.store_run_usage(result)

# Continue conversation
result = await Runner.run(
    agent,
    "What state is it in?",
    session=session
)
print(result.final_output)  # "California"
await session.store_run_usage(result)
```

## Initialization

```python
from agents.extensions.memory import AdvancedSQLiteSession

# Basic initialization
session = AdvancedSQLiteSession(
    session_id="my_conversation",
    create_tables=True  # Auto-create advanced tables
)

# With persistent storage
session = AdvancedSQLiteSession(
    session_id="user_123",
    db_path="path/to/conversations.db",
    create_tables=True
)

# With custom logger
import logging
logger = logging.getLogger("my_app")
session = AdvancedSQLiteSession(
    session_id="session_456",
    create_tables=True,
    logger=logger
)
```

### Parameters

*   **session_id (str):** Unique identifier for the conversation session
*   **db_path (str | Path):** Path to SQLite database file. Defaults to `:memory:` for in-memory storage
*   **create_tables (bool):** Whether to automatically create the advanced tables. Defaults to `False`
*   **logger (logging.Logger | None):** Custom logger for the session. Defaults to module logger

## Usage tracking

`AdvancedSQLiteSession` provides detailed usage analytics by storing token usage data per conversation turn. This is entirely dependent on the `store_run_usage` method being called after each agent run.

### Storing usage data

```python
# After each agent run, store the usage data
result = await Runner.run(agent, "Hello", session=session)
await session.store_run_usage(result)

# This stores:
# - Total tokens used
# - Input/output token breakdown
# - Request count
# - Detailed JSON token information (if available)
```

### Retrieving usage statistics

```python
# Get session-level usage (all branches)
session_usage = await session.get_session_usage()
if session_usage:
    print(f"Total requests: {session_usage['requests']}")
    print(f"Total tokens: {session_usage['total_tokens']}")
    print(f"Input tokens: {session_usage['input_tokens']}")
    print(f"Output tokens: {session_usage['output_tokens']}")
    print(f"Total turns: {session_usage['total_turns']}")

# Get usage for specific branch
branch_usage = await session.get_session_usage(branch_id="main")

# Get usage by turn
turn_usage = await session.get_turn_usage()
for turn_data in turn_usage:
    print(f"Turn {turn_data['user_turn_number']}: {turn_data['total_tokens']} tokens")
    if turn_data['input_tokens_details']:
        print(f"  Input details: {turn_data['input_tokens_details']}")
    if turn_data['output_tokens_details']:
        print(f"  Output details: {turn_data['output_tokens_details']}")

# Get usage for specific turn
turn_2_usage = await session.get_turn_usage(user_turn_number=2)
```

## Conversation branching

One of the key features of `AdvancedSQLiteSession` is the ability to create conversation branches from any user message, allowing you to explore alternative conversation paths.

### Creating branches

```python
# Get available turns for branching
turns = await session.get_conversation_turns()
for turn in turns:
    print(f"Turn {turn['turn']}: {turn['content']}")
    print(f"Can branch: {turn['can_branch']}")

# Create a branch from turn 2
branch_id = await session.create_branch_from_turn(2)
print(f"Created branch: {branch_id}")

# Create a branch with custom name
branch_id = await session.create_branch_from_turn(
    2, 
    branch_name="alternative_path"
)

# Create branch by searching for content
branch_id = await session.create_branch_from_content(
    "weather", 
    branch_name="weather_focus"
)
```

### Branch management

```python
# List all branches
branches = await session.list_branches()
for branch in branches:
    current = " (current)" if branch["is_current"] else ""
    print(f"{branch['branch_id']}: {branch['user_turns']} turns, {branch['message_count']} messages{current}")

# Switch between branches
await session.switch_to_branch("main")
await session.switch_to_branch(branch_id)

# Delete a branch
await session.delete_branch(branch_id, force=True)  # force=True allows deleting current branch
```

### Branch workflow example

```python
# Original conversation
result = await Runner.run(agent, "What's the capital of France?", session=session)
await session.store_run_usage(result)

result = await Runner.run(agent, "What's the weather like there?", session=session)
await session.store_run_usage(result)

# Create branch from turn 2 (weather question)
branch_id = await session.create_branch_from_turn(2, "weather_focus")

# Continue in new branch with different question
result = await Runner.run(
    agent, 
    "What are the main tourist attractions in Paris?", 
    session=session
)
await session.store_run_usage(result)

# Switch back to main branch
await session.switch_to_branch("main")

# Continue original conversation
result = await Runner.run(
    agent, 
    "How expensive is it to visit?", 
    session=session
)
await session.store_run_usage(result)
```

## Structured queries

`AdvancedSQLiteSession` provides several methods for analyzing conversation structure and content.

### Conversation analysis

```python
# Get conversation organized by turns
conversation_by_turns = await session.get_conversation_by_turns()
for turn_num, items in conversation_by_turns.items():
    print(f"Turn {turn_num}: {len(items)} items")
    for item in items:
        if item["tool_name"]:
            print(f"  - {item['type']} (tool: {item['tool_name']})")
        else:
            print(f"  - {item['type']}")

# Get tool usage statistics
tool_usage = await session.get_tool_usage()
for tool_name, count, turn in tool_usage:
    print(f"{tool_name}: used {count} times in turn {turn}")

# Find turns by content
matching_turns = await session.find_turns_by_content("weather")
for turn in matching_turns:
    print(f"Turn {turn['turn']}: {turn['content']}")
```

## Message structure

The session automatically tracks message structure including:

*   Message types (user, assistant, tool_call, etc.)
*   Tool names for tool calls
*   Turn numbers and sequence numbers
*   Branch associations
*   Timestamps

## Database schema

`AdvancedSQLiteSession` extends the basic SQLite schema with two additional tables:

**message_structure table**

```sql
CREATE TABLE message_structure (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    message_id INTEGER NOT NULL,
    branch_id TEXT NOT NULL DEFAULT 'main',
    message_type TEXT NOT NULL,
    sequence_number INTEGER NOT NULL,
    user_turn_number INTEGER,
    branch_turn_number INTEGER,
    tool_name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES agent_sessions(session_id) ON DELETE CASCADE,
    FOREIGN KEY (message_id) REFERENCES agent_messages(id) ON DELETE CASCADE
);
```

**turn_usage table**

```sql
CREATE TABLE turn_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    branch_id TEXT NOT NULL DEFAULT 'main',
    user_turn_number INTEGER NOT NULL,
    requests INTEGER DEFAULT 0,
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    input_tokens_details JSON,
    output_tokens_details JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES agent_sessions(session_id) ON DELETE CASCADE,
    UNIQUE(session_id, branch_id, user_turn_number)
);
```

## Complete example

Check out the complete example for a comprehensive demonstration of all features.

## API Reference

*   `AdvancedSQLiteSession` - Main class
*   `Session` - Base session protocol

---

# Encrypted Sessions

`EncryptedSession` provides transparent encryption for any session implementation, securing conversation data with automatic expiration of old items.

## Features

*   **Transparent encryption:** Wraps any session with Fernet encryption
*   **Per-session keys:** Uses HKDF key derivation for unique encryption per session
*   **Automatic expiration:** Old items are silently skipped when TTL expires
*   **Drop-in replacement:** Works with any existing session implementation

## Installation

Encrypted sessions require the `encrypt` extra:

```bash
pip install openai-agents[encrypt]
```

## Quick start

```python
import asyncio
from agents import Agent, Runner
from agents.extensions.memory import EncryptedSession, SQLAlchemySession

async def main():
    agent = Agent("Assistant")

    # Create underlying session
    underlying_session = SQLAlchemySession.from_url(
        "user-123",
        url="sqlite+aiosqlite:///:memory:",
        create_tables=True
    )

    # Wrap with encryption
    session = EncryptedSession(
        session_id="user-123",
        underlying_session=underlying_session,
        encryption_key="your-secret-key-here",
        ttl=600  # 10 minutes
    )

    result = await Runner.run(agent, "Hello", session=session)
    print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())
```

## Configuration

### Encryption key

The encryption key can be either a Fernet key or any string:

```python
from agents.extensions.memory import EncryptedSession

# Using a Fernet key (base64-encoded)
session = EncryptedSession(
    session_id="user-123",
    underlying_session=underlying_session,
    encryption_key="your-fernet-key-here",
    ttl=600
)

# Using a raw string (will be derived to a key)
session = EncryptedSession(
    session_id="user-123", 
    underlying_session=underlying_session,
    encryption_key="my-secret-password",
    ttl=600
)
```

### TTL (Time To Live)

Set how long encrypted items remain valid:

```python
# Items expire after 1 hour
session = EncryptedSession(
    session_id="user-123",
    underlying_session=underlying_session,
    encryption_key="secret",
    ttl=3600  # 1 hour in seconds
)

# Items expire after 1 day
session = EncryptedSession(
    session_id="user-123",
    underlying_session=underlying_session,
    encryption_key="secret", 
    ttl=86400  # 24 hours in seconds
)
```

## Usage with different session types

### With SQLite sessions

```python
from agents import SQLiteSession
from agents.extensions.memory import EncryptedSession

# Create encrypted SQLite session
underlying = SQLiteSession("user-123", "conversations.db")

session = EncryptedSession(
    session_id="user-123",
    underlying_session=underlying,
    encryption_key="secret-key"
)
```

### With SQLAlchemy sessions

```python
from agents.extensions.memory import EncryptedSession, SQLAlchemySession

# Create encrypted SQLAlchemy session
underlying = SQLAlchemySession.from_url(
    "user-123",
    url="postgresql+asyncpg://user:pass@localhost/db",
    create_tables=True
)

session = EncryptedSession(
    session_id="user-123",
    underlying_session=underlying,
    encryption_key="secret-key"
)
```

## Advanced Session Features

When using `EncryptedSession` with advanced session implementations like `AdvancedSQLiteSession`, note that:

*   Methods like `find_turns_by_content()` won't work effectively since message content is encrypted
*   Content-based searches operate on encrypted data, limiting their effectiveness

### Key derivation

`EncryptedSession` uses HKDF (HMAC-based Key Derivation Function) to derive unique encryption keys per session:

*   **Master key:** Your provided encryption key
*   **Session salt:** The session ID
*   **Info string:** "agents.session-store.hkdf.v1"
*   **Output:** 32-byte Fernet key

This ensures that: 
*   Each session has a unique encryption key
*   Keys cannot be derived without the master key
*   Session data cannot be decrypted across different sessions

### Automatic expiration

When items exceed the TTL, they are automatically skipped during retrieval:

```python
# Items older than TTL are silently ignored
items = await session.get_items()  # Only returns non-expired items

# Expired items don't affect session behavior
result = await Runner.run(agent, "Continue conversation", session=session)
```

## API Reference

*   `EncryptedSession` - Main class
*   `Session` - Base session protocol

---

SQLAlchemySession
Bases: SessionABC

SQLAlchemy implementation of :pyclass:agents.memory.session.Session.

Source code in src/agents/extensions/memory/sqlalchemy_session.py
__init__

__init__(
    session_id: str,
    *,
    engine: AsyncEngine,
    create_tables: bool = False,
    sessions_table: str = "agent_sessions",
    messages_table: str = "agent_messages",
)
Initializes a new SQLAlchemySession.

Parameters:

Name	Type	Description	Default
session_id	str	Unique identifier for the conversation.	required
engine	AsyncEngine	A pre-configured SQLAlchemy async engine. The engine must be created with an async driver (e.g., 'postgresql+asyncpg://', 'mysql+aiomysql://', or 'sqlite+aiosqlite://').	required
create_tables	bool	Whether to automatically create the required tables and indexes. Defaults to False for production use. Set to True for development and testing when migrations aren't used.	False
sessions_table	str	Override the default table name for sessions if needed.	'agent_sessions'
messages_table	str	Override the default table name for messages if needed.	'agent_messages'
Source code in src/agents/extensions/memory/sqlalchemy_session.py
from_url classmethod

from_url(
    session_id: str,
    *,
    url: str,
    engine_kwargs: dict[str, Any] | None = None,
    **kwargs: Any,
) -> SQLAlchemySession
Create a session from a database URL string.

Parameters:

Name	Type	Description	Default
session_id	str	Conversation ID.	required
url	str	Any SQLAlchemy async URL, e.g. "postgresql+asyncpg://user:pass@host/db".	required
engine_kwargs	dict[str, Any] | None	Additional keyword arguments forwarded to sqlalchemy.ext.asyncio.create_async_engine.	None
**kwargs	Any	Additional keyword arguments forwarded to the main constructor (e.g., create_tables, custom table names, etc.).	{}
Returns:

Name	Type	Description
SQLAlchemySession	SQLAlchemySession	An instance of SQLAlchemySession connected to the specified database.
Source code in src/agents/extensions/memory/sqlalchemy_session.py
get_items async

get_items(
    limit: int | None = None,
) -> list[TResponseInputItem]
Retrieve the conversation history for this session.

Parameters:

Name	Type	Description	Default
limit	int | None	Maximum number of items to retrieve. If None, retrieves all items. When specified, returns the latest N items in chronological order.	None
Returns:

Type	Description
list[TResponseInputItem]	List of input items representing the conversation history
Source code in src/agents/extensions/memory/sqlalchemy_session.py
add_items async

add_items(items: list[TResponseInputItem]) -> None
Add new items to the conversation history.

Parameters:

Name	Type	Description	Default
items	list[TResponseInputItem]	List of input items to add to the history	required
Source code in src/agents/extensions/memory/sqlalchemy_session.py
pop_item async

pop_item() -> TResponseInputItem | None
Remove and return the most recent item from the session.

Returns:

Type	Description
TResponseInputItem | None	The most recent item if it exists, None if the session is empty
Source code in src/agents/extensions/memory/sqlalchemy_session.py
clear_session async

clear_session() -> None
Clear all items for this session.

Source code in src/agents/extensions/memory/sqlalchemy_session.py