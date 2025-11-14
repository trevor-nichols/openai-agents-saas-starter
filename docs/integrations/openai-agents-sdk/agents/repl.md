repl
run_demo_loop async

run_demo_loop(
    agent: Agent[Any],
    *,
    stream: bool = True,
    context: TContext | None = None,
) -> None
Run a simple REPL loop with the given agent.

This utility allows quick manual testing and debugging of an agent from the command line. Conversation state is preserved across turns. Enter exit or quit to stop the loop.

Parameters:

Name	Type	Description	Default
agent	Agent[Any]	The starting agent to run.	required
stream	bool	Whether to stream the agent output.	True
context	TContext | None	Additional context information to pass to the runner.	None
Source code in src/agents/repl.py