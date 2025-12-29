'use client';

import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { SectionHeader } from '@/components/ui/foundation';

import { TEAM_SETTINGS_COPY } from './constants';
import { MembersPanel, InvitesPanel } from './components';

export function TeamSettingsWorkspace() {
  return (
    <section className="space-y-8">
      <SectionHeader
        eyebrow={TEAM_SETTINGS_COPY.header.eyebrow}
        title={TEAM_SETTINGS_COPY.header.title}
        description={TEAM_SETTINGS_COPY.header.description}
      />

      <Tabs defaultValue="members" className="space-y-6">
        <TabsList className="grid w-full max-w-md grid-cols-2">
          <TabsTrigger value="members">Members</TabsTrigger>
          <TabsTrigger value="invites">Invites</TabsTrigger>
        </TabsList>

        <TabsContent value="members">
          <MembersPanel />
        </TabsContent>

        <TabsContent value="invites">
          <InvitesPanel />
        </TabsContent>
      </Tabs>
    </section>
  );
}
