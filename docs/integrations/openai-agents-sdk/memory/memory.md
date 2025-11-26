Memory
Session
Bases: Protocol

Protocol for session implementations.

Session stores conversation history for a specific session, allowing agents to maintain context without requiring explicit manual memory management.

Source code in src/agents/memory/session.py
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
Source code in src/agents/memory/session.py
add_items async

add_items(items: list[TResponseInputItem]) -> None
Add new items to the conversation history.

Parameters:

Name	Type	Description	Default
items	list[TResponseInputItem]	List of input items to add to the history	required
Source code in src/agents/memory/session.py
pop_item async

pop_item() -> TResponseInputItem | None
Remove and return the most recent item from the session.

Returns:

Type	Description
TResponseInputItem | None	The most recent item if it exists, None if the session is empty
Source code in src/agents/memory/session.py
clear_session async

clear_session() -> None
Clear all items for this session.

Source code in src/agents/memory/session.py
SQLiteSession
Bases: SessionABC

SQLite-based implementation of session storage.

This implementation stores conversation history in a SQLite database. By default, uses an in-memory database that is lost when the process ends. For persistent storage, provide a file path.

Source code in src/agents/memory/sqlite_session.py
__init__

__init__(
    session_id: str,
    db_path: str | Path = ":memory:",
    sessions_table: str = "agent_sessions",
    messages_table: str = "agent_messages",
)
Initialize the SQLite session.

Parameters:

Name	Type	Description	Default
session_id	str	Unique identifier for the conversation session	required
db_path	str | Path	Path to the SQLite database file. Defaults to ':memory:' (in-memory database)	':memory:'
sessions_table	str	Name of the table to store session metadata. Defaults to 'agent_sessions'	'agent_sessions'
messages_table	str	Name of the table to store message data. Defaults to 'agent_messages'	'agent_messages'
Source code in src/agents/memory/sqlite_session.py
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
Source code in src/agents/memory/sqlite_session.py
add_items async

add_items(items: list[TResponseInputItem]) -> None
Add new items to the conversation history.

Parameters:

Name	Type	Description	Default
items	list[TResponseInputItem]	List of input items to add to the history	required
Source code in src/agents/memory/sqlite_session.py
pop_item async

pop_item() -> TResponseInputItem | None
Remove and return the most recent item from the session.

Returns:

Type	Description
TResponseInputItem | None	The most recent item if it exists, None if the session is empty
Source code in src/agents/memory/sqlite_session.py
clear_session async

clear_session() -> None
Clear all items for this session.

Source code in src/agents/memory/sqlite_session.py
close

close() -> None
Close the database connection.

Source code in src/agents/memory/sqlite_session.py