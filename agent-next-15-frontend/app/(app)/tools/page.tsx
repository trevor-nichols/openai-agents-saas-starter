// File Path: app/(app)/tools/page.tsx
// Description: Placeholder tool catalog page.
// Sections:
// - Imports: Feature orchestrator.
// - ToolsPage component: Thin wrapper around the tools feature.

import { ToolsCatalog } from '@/features/tools';

export const metadata = {
  title: 'Tools | Anything Agents',
};

export default function ToolsPage() {
  return <ToolsCatalog />;
}

