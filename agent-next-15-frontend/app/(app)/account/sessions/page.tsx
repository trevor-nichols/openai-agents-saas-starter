// File Path: app/(app)/account/sessions/page.tsx
// Description: Placeholder page for managing active sessions.
// Sections:
// - Imports: Account feature orchestrator.
// - SessionsPage component: Thin wrapper for the sessions surface.

import { SessionsPanel } from '@/features/account';

export const metadata = {
  title: 'Sessions | Anything Agents',
};

export default function SessionsPage() {
  return <SessionsPanel />;
}

