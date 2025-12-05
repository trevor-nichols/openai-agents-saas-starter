export function formatConversationLabel(conversationId?: string | null) {
  if (!conversationId) {
    return 'Start a new conversation to brief your agent.';
  }
  return `Conversation ${conversationId.substring(0, 12)}…`;
}

export function normalizeAgentLabel(agent: string) {
  return agent.replace(/_/g, ' ');
}

export function formatAttachmentSize(size?: number | null) {
  if (!size || size <= 0) return '';
  if (size < 1024) return `${size} B`;
  const kb = size / 1024;
  if (kb < 1024) return `${kb.toFixed(1)} KB`;
  return `${(kb / 1024).toFixed(1)} MB`;
}

export function formatStructuredOutput(value: unknown) {
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
}
