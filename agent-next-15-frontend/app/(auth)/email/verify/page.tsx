// File Path: app/(auth)/email/verify/page.tsx
// Description: Placeholder email verification status page.
// Sections:
// - VerifyEmailPage component: Indicates future UX and shows token snippet if present.

interface VerifyEmailPageProps {
  searchParams?: Record<string, string | string[] | undefined>;
}

export default function VerifyEmailPage({ searchParams }: VerifyEmailPageProps) {
  const token = typeof searchParams?.token === 'string' ? searchParams.token : undefined;

  return (
    <div className="space-y-4 text-center">
      <h1 className="text-2xl font-semibold text-slate-900">Verify your email address</h1>
      <p className="text-sm text-slate-500">
        We&apos;ll confirm your verification status here and allow resending the email if needed.
      </p>
      {token ? (
        <p className="text-xs text-slate-400">Token detected: {token.slice(0, 8)}…</p>
      ) : (
        <p className="text-xs text-amber-500">Add a verification token to the URL to complete the flow.</p>
      )}
    </div>
  );
}

