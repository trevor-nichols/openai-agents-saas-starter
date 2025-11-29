export const CHAT_COPY = {
  header: {
    eyebrow: 'Workspace',
    title: 'Anything Agent Chat',
    descriptionEmpty: 'Start a new conversation to brief your agent.',
  },
  sidebar: {
    heading: 'Conversations',
    newConversation: 'New conversation',
  },
  toolDrawer: {
    title: 'Agent tools',
    description: (agentLabel: string) => `Registry context for ${agentLabel}.`,
  },
  transcript: {
    exportInfoTitle: 'Transcript export is on the roadmap',
    exportInfoDescription: 'We will notify you once CSV/PDF export is available.',
  },
  errors: {
    conversationDelete: 'Delete this conversation permanently?',
    workspaceErrorTitle: 'Chat workspace error',
  },
} as const;
