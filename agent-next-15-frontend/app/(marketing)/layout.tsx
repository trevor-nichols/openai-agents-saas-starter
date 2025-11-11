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

const marketingNav = [
  { href: '/', label: 'Home' },
  { href: '/pricing', label: 'Pricing' },
  { href: '/features', label: 'Features' },
  { href: '/docs', label: 'Docs' },
];

const footerLinks = [
  { href: '/privacy', label: 'Privacy' },
  { href: '/terms', label: 'Terms' },
  { href: '/status', label: 'Status' },
];

// --- MarketingLayout component ---
// Provides the Johnny Ive-inspired marketing shell with translucent chrome.
export default function MarketingLayout({ children }: MarketingLayoutProps) {
  return (
    <div className="relative flex min-h-screen flex-col overflow-hidden bg-background text-foreground">
      <div className="pointer-events-none absolute inset-0 -z-10 bg-[radial-gradient(circle_at_top,_rgba(110,181,255,0.18),_transparent_45%)]" />

      <header className="sticky top-0 z-40 border-b border-white/10 bg-background/80 backdrop-blur-glass">
        <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-4">
          <Link href="/" className="text-lg font-semibold tracking-tight">
            Anything Agents
          </Link>

          <nav aria-label="Marketing primary navigation" className="hidden items-center gap-6 text-sm font-medium md:flex">
            {marketingNav.map((item) => (
              <Link key={item.href} href={item.href} className="text-foreground/70 transition-colors duration-quick ease-apple hover:text-foreground">
                {item.label}
              </Link>
            ))}
          </nav>

          <Link
            href="/login"
            className="rounded-pill border border-white/20 px-4 py-2 text-sm font-semibold text-foreground transition duration-quick ease-apple hover:border-white/40"
          >
            Sign in
          </Link>
        </div>
      </header>

      <main className="flex-1">
        <div className="mx-auto w-full max-w-6xl px-6 py-16">
          {children}
        </div>
      </main>

      <footer className="border-t border-white/10 bg-background/80 py-8 text-sm text-foreground/70 backdrop-blur-glass">
        <div className="mx-auto flex w-full max-w-6xl flex-col gap-4 px-6 md:flex-row md:items-center md:justify-between">
          <p>&copy; {new Date().getFullYear()} Anything Agents. All rights reserved.</p>
          <div className="flex flex-wrap items-center gap-4">
            {footerLinks.map((link) => (
              <Link key={link.href} href={link.href} className="transition-colors duration-quick ease-apple hover:text-foreground">
                {link.label}
              </Link>
            ))}
          </div>
        </div>
      </footer>
    </div>
  );
}
