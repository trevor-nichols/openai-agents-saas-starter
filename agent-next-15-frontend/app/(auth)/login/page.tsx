// File Path: app/(auth)/login/page.tsx
// Description: Sign-in page that renders within the shared auth layout.
// Sections:
// - LoginPage component: Passes redirect information to the LoginForm.

import { LoginForm } from '@/components/auth/LoginForm';

interface LoginPageProps {
  searchParams?: Record<string, string | string[] | undefined>;
}

export default function LoginPage({ searchParams }: LoginPageProps) {
  const redirectTo = typeof searchParams?.redirectTo === 'string' ? searchParams?.redirectTo : undefined;

  return (
    <div className="space-y-6 text-center">
      <header className="space-y-2">
        <h1 className="text-2xl font-semibold text-slate-900">Sign in to Anything Agents</h1>
        <p className="text-sm text-slate-500">Use your organization credentials to continue.</p>
      </header>

      <LoginForm redirectTo={redirectTo} />
    </div>
  );
}
