// File Path: app/(app)/(workspace)/chat/page.tsx
// Description: Chat workspace page – delegates to the chat feature orchestrator.
// Sections:
// - Imports: Feature orchestrator.
// - Component: Renders the chat workspace within the authenticated shell.

import { ChatWorkspace } from '@/features/chat';

export default function ChatWorkspacePage() {
  return <ChatWorkspace />;
}

