// File Path: app/(auth)/password/reset/page.tsx
// Description: Placeholder page for redeeming password reset tokens.
// Sections:
// - ResetPasswordPage component: Placeholder until final form is implemented.

interface ResetPasswordPageProps {
  searchParams?: Record<string, string | string[] | undefined>;
}

export default function ResetPasswordPage({ searchParams }: ResetPasswordPageProps) {
  const token = typeof searchParams?.token === 'string' ? searchParams.token : undefined;

  return (
    <div className="space-y-4 text-center">
      <h1 className="text-2xl font-semibold text-slate-900">Reset your password</h1>
      <p className="text-sm text-slate-500">
        The secure reset form will appear here. We&apos;ll validate your token and let you set a new password.
      </p>
      {token ? (
        <p className="text-xs text-slate-400">Token detected: {token.slice(0, 8)}…</p>
      ) : (
        <p className="text-xs text-amber-500">No token present in the URL.</p>
      )}
    </div>
  );
}

