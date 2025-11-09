// File Path: app/(agent)/layout.tsx
// Description: This file defines the layout specifically for the (agent) route group.
// It allows for shared UI components or context for all agent-related pages.
// Dependencies:
// - React: For creating the layout component.
// - app/layout.tsx: This layout is nested within the root layout.
// Dependents:
// - All page.tsx files within the app/(agent)/ directory.

import React from 'react';

import { SilentRefresh } from '@/components/auth/SilentRefresh';

// --- AgentLayout Component ---
// This layout component wraps all pages within the (agent) route group.
// It can be used to add UI elements common to all agent pages (e.g., a sidebar, header).
export default function AgentLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <>
      <SilentRefresh />
      {children}
    </>
  );
}
