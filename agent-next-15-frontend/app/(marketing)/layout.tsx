// File Path: app/(marketing)/layout.tsx
// Description: Shared layout for all marketing-facing routes (landing, pricing, docs).
// Sections:
// - Imports: External dependencies used by the layout.
// - Navigation configuration: Static navigation links for the marketing shell.
// - MarketingLayout component: Renders header, main content slot, and footer.

import Link from 'next/link';

interface MarketingLayoutProps {
  children: React.ReactNode;
}

// --- Navigation configuration ---
// Centralized list of links rendered in the marketing header navigation.
const marketingNav = [
  { href: '/', label: 'Home' },
  { href: '/pricing', label: 'Pricing' },
  { href: '/features', label: 'Features' },
  { href: '/login', label: 'Sign in' },
];

// --- MarketingLayout component ---
// Provides the public marketing shell with a simple header and footer.
export default function MarketingLayout({ children }: MarketingLayoutProps) {
  return (
    <div className="flex min-h-screen flex-col bg-background text-foreground">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-4">
          <Link href="/" className="text-lg font-semibold">
            Anything Agents
          </Link>

          <nav aria-label="Marketing primary navigation" className="flex items-center gap-6 text-sm font-medium">
            {marketingNav.map((item) => (
              <Link key={item.href} href={item.href} className="text-slate-600 transition hover:text-slate-900">
                {item.label}
              </Link>
            ))}
          </nav>
        </div>
      </header>

      <main className="flex-1">
        {children}
      </main>

      <footer className="border-t border-slate-200 bg-slate-50 py-8 text-sm text-slate-500">
        <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-6">
          <p>&copy; {new Date().getFullYear()} Anything Agents. All rights reserved.</p>
          <div className="flex items-center gap-4">
            <Link href="/docs" className="hover:text-slate-700">
              Documentation
            </Link>
            <Link href="/pricing" className="hover:text-slate-700">
              Pricing
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
}

