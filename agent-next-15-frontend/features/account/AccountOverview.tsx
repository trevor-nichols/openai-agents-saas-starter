// File Path: features/account/AccountOverview.tsx
// Description: Client-side tabbed account view bundling profile, security, sessions, and automation placeholders.

'use client';

import Link from 'next/link';

import { Button } from '@/components/ui/button';
import { SectionHeader } from '@/components/ui/foundation';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

import { ProfilePanel } from './components/ProfilePanel';
import { SecurityPanel } from './components/SecurityPanel';
import { ServiceAccountsPanel } from './components/ServiceAccountsPanel';
import { SessionsPanel } from './components/SessionsPanel';
import { ACCOUNT_COPY, ACCOUNT_TABS } from './constants';
import { useAccountTabs } from './hooks/useAccountTabs';
import type { AccountOverviewProps } from './types';

export function AccountOverview({ initialTab = 'profile' }: AccountOverviewProps) {
  const { tab, handleTabChange } = useAccountTabs(initialTab);

  return (
    <section className="space-y-8">
      <SectionHeader
        eyebrow={ACCOUNT_COPY.header.eyebrow}
        title={ACCOUNT_COPY.header.title}
        description={ACCOUNT_COPY.header.description}
        actions={
          <Button variant="outline" size="sm" asChild>
            <Link href="/billing">{ACCOUNT_COPY.header.ctaLabel}</Link>
          </Button>
        }
      />

      <Tabs value={tab} onValueChange={handleTabChange} className="space-y-6">
        <TabsList className="flex flex-wrap gap-2 bg-transparent p-0">
          {ACCOUNT_TABS.map((option) => (
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
          <ServiceAccountsPanel />
        </TabsContent>
      </Tabs>
    </section>
  );
}
