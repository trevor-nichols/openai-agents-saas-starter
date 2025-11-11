// File Path: app/(auth)/layout.tsx
// Description: Shared layout for authentication routes, providing consistent framing.
// Sections:
// - AuthLayout component: Centers card-style content with gradient backdrop.

interface AuthLayoutProps {
  children: React.ReactNode;
}

// --- AuthLayout component ---
// Wraps auth pages in a frosted glass card with centered composition.
export default function AuthLayout({ children }: AuthLayoutProps) {
  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-background text-foreground">
      <div className="pointer-events-none absolute inset-0 -z-10 bg-[radial-gradient(circle_at_top,_rgba(110,181,255,0.18),_transparent_55%)]" />
      <div className="pointer-events-none absolute inset-y-0 left-1/2 h-[120%] w-[75%] -translate-x-1/2 rounded-full bg-[radial-gradient(circle,_rgba(75,209,123,0.12),_transparent_60%)] blur-3xl" />

      <div className="relative w-full max-w-2xl px-4 py-16 sm:px-6 lg:px-8">{children}</div>
    </div>
  );
}
