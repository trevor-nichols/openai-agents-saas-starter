// File Path: app/(auth)/layout.tsx
// Description: Shared layout for authentication routes, providing consistent framing.
// Sections:
// - AuthLayout component: Centers card-style content with gradient backdrop.

interface AuthLayoutProps {
  children: React.ReactNode;
}

// --- AuthLayout component ---
// Wraps auth pages with a gradient background and constrained content width.
export default function AuthLayout({ children }: AuthLayoutProps) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-slate-100 to-slate-200 py-12">
      <div className="mx-auto w-full max-w-md px-4">
        <div className="rounded-3xl border border-slate-200 bg-white p-10 shadow-2xl">
          {children}
        </div>
      </div>
    </div>
  );
}

