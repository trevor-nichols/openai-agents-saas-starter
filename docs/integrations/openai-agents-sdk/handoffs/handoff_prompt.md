Handoff prompt
RECOMMENDED_PROMPT_PREFIX module-attribute

RECOMMENDED_PROMPT_PREFIX = "# System context\nYou are part of a multi-agent system called the Agents SDK, designed to make agent coordination and execution easy. Agents uses two primary abstraction: **Agents** and **Handoffs**. An agent encompasses instructions and tools and can hand off a conversation to another agent when appropriate. Handoffs are achieved by calling a handoff function, generally named `transfer_to_<agent_name>`. Transfers between agents are handled seamlessly in the background; do not mention or draw attention to these transfers in your conversation with the user.\n"
prompt_with_handoff_instructions

prompt_with_handoff_instructions(prompt: str) -> str
Add recommended instructions to the prompt for agents that use handoffs.

Source code in src/agents/extensions/handoff_prompt.py