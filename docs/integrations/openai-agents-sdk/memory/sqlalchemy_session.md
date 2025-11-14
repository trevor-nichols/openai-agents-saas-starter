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