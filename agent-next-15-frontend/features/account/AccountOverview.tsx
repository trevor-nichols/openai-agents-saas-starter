// File Path: features/account/AccountOverview.tsx
// Description: Client-side tabbed account view bundling profile, security, sessions, and automation placeholders.

'use client';

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { usePathname, useRouter, useSearchParams } from 'next/navigation';

import { Button } from '@/components/ui/button';
import { GlassPanel, SectionHeader } from '@/components/ui/foundation';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

import { ProfilePanel } from './ProfilePanel';
import { SecurityPanel } from './SecurityPanel';
import { SessionsPanel } from './SessionsPanel';

const TAB_OPTIONS = [
  { key: 'profile', label: 'Profile' },
  { key: 'security', label: 'Security' },
  { key: 'sessions', label: 'Sessions' },
  { key: 'automation', label: 'Automation' },
] as const;

type TabKey = (typeof TAB_OPTIONS)[number]['key'];

function isTabKey(value: string): value is TabKey {
  return TAB_OPTIONS.some((option) => option.key === value);
}

interface AccountOverviewProps {
  initialTab?: string;
}

export function AccountOverview({ initialTab = 'profile' }: AccountOverviewProps) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const sanitizedTab = useMemo(() => (isTabKey(initialTab) ? initialTab : 'profile'), [initialTab]);
  const [tab, setTab] = useState<TabKey>(sanitizedTab);

  useEffect(() => {
    setTab(sanitizedTab);
  }, [sanitizedTab]);

  const handleTabChange = (value: string) => {
    if (!isTabKey(value)) return;
    setTab(value);

    if (typeof window === 'undefined') {
      return;
    }

    const params = new URLSearchParams(searchParams?.toString());
    params.set('tab', value);
    const nextUrl = `${pathname}?${params.toString()}`;
    router.replace(nextUrl, { scroll: false });
  };

  return (
    <section className="space-y-8">
      <SectionHeader
        eyebrow="Account"
        title="Manage your workspace profile"
        description="Update profile metadata, tighten security controls, and review session activity in one place."
        actions={
          <Button variant="outline" size="sm" asChild>
            <Link href="/billing">Billing settings</Link>
          </Button>
        }
      />

      <Tabs value={tab} onValueChange={handleTabChange} className="space-y-6">
        <TabsList className="flex flex-wrap gap-2 bg-transparent p-0">
          {TAB_OPTIONS.map((option) => (
            <TabsTrigger key={option.key} value={option.key} className="rounded-full px-4 py-2">
              {option.label}
            </TabsTrigger>
          ))}
        </TabsList>

        <TabsContent value="profile">
          <ProfilePanel />
        </TabsContent>

        <TabsContent value="security">
          <SecurityPanel />
        </TabsContent>

        <TabsContent value="sessions">
          <SessionsPanel />
        </TabsContent>

        <TabsContent value="automation">
          <AutomationPlaceholder />
        </TabsContent>
      </Tabs>
    </section>
  );
}

function AutomationPlaceholder() {
  return (
    <GlassPanel className="space-y-4">
      <SectionHeader
        eyebrow="Automation"
        title="Service-account UI coming soon"
        description="Machine credential issuance stays in the CLI until the backend exposes list/revoke APIs."
      />
      <Alert>
        <AlertTitle>Use the Starter CLI today</AlertTitle>
        <AlertDescription className="space-y-2 text-sm text-foreground/70">
          <p>
            Generate or revoke service-account tokens via
            <code className="ml-1 rounded bg-muted px-2 py-1 text-xs font-mono">starter_cli auth tokens issue-service-account</code>
            while we finish the audited API surface.
          </p>
          <p>
            Track progress in <Link className="underline" href="/docs">docs/trackers/ISSUE_TRACKER.md · FE-016</Link>.
          </p>
        </AlertDescription>
      </Alert>
    </GlassPanel>
  );
}
