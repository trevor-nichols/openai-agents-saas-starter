// File Path: app/(app)/conversations/page.tsx
// Description: Placeholder conversations list that will evolve into a data table.
// Sections:
// - Imports: Feature orchestrator.
// - ConversationsPage component: Thin wrapper mapping to the feature entry point.

import { ConversationsHub } from '@/features/conversations';

export const metadata = {
  title: 'Conversations | Anything Agents',
};

export default function ConversationsPage() {
  return <ConversationsHub />;
}

