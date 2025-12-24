import type { SelectOption } from '../types';

export interface AgentOptionSource {
  name: string;
  display_name?: string | null;
  description?: string | null;
}

export interface ConversationOptionSource {
  id: string;
  display_name?: string | null;
  title?: string | null;
  last_message_preview?: string | null;
}

export function buildAgentOptions(agents: readonly AgentOptionSource[]): SelectOption[] {
  return agents.map((agent) => ({
    value: agent.name,
    label: agent.display_name ?? agent.name,
    description: agent.description ?? null,
  }));
}

export function buildConversationOptions(
  conversations: readonly ConversationOptionSource[],
): SelectOption[] {
  return conversations.map((conversation) => ({
    value: conversation.id,
    label:
      conversation.display_name ??
      conversation.title ??
      conversation.last_message_preview ??
      `Conversation ${conversation.id.slice(0, 8)}`,
    description: conversation.last_message_preview ?? null,
  }));
}
