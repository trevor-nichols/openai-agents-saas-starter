export function formatConversationLabel(conversationId?: string | null) {
  if (!conversationId) {
    return 'Start a new conversation to brief your agent.';
  }
  return `Conversation ${conversationId.substring(0, 12)}…`;
}

export function normalizeAgentLabel(agent: string) {
  return agent.replace(/_/g, ' ');
}
