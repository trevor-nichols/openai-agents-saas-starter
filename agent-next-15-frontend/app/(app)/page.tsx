// File Path: app/(app)/page.tsx
// Description: Redirects the base app path to the dashboard.
// Sections:
// - AppIndexPage component: Performs a server-side redirect to /dashboard.

import { redirect } from 'next/navigation';

export default function AppIndexPage() {
  redirect('/dashboard');
}

