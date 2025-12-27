'use client';

import { useMemo } from 'react';

import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { GlassPanel, InlineTag, SectionHeader } from '@/components/ui/foundation';
import type { CurrentUserProfileResponseData } from '@/lib/api/client/types.gen';

interface ProfileIdentityCardProps {
  profile: CurrentUserProfileResponseData;
}

function resolveDisplayName(profile: CurrentUserProfileResponseData): string {
  if (profile.display_name?.trim()) {
    return profile.display_name;
  }
  const parts = [profile.given_name, profile.family_name].filter((value) => value && value.trim());
  if (parts.length > 0) {
    return parts.join(' ');
  }
  return profile.email ?? 'Unnamed user';
}

export function ProfileIdentityCard({ profile }: ProfileIdentityCardProps) {
  const displayName = resolveDisplayName(profile);

  const initials = useMemo(() => {
    if (!displayName) {
      return 'AA';
    }
    return displayName
      .split(' ')
      .filter(Boolean)
      .map((chunk) => chunk[0]?.toUpperCase())
      .slice(0, 2)
      .join('');
  }, [displayName]);

  return (
    <GlassPanel className="space-y-6">
      <SectionHeader
        title="Identity"
        description="Profile metadata for this signed-in human."
        actions={
          <InlineTag tone={profile.email_verified ? 'positive' : 'warning'}>
            {profile.email_verified ? 'Email verified' : 'Verification pending'}
          </InlineTag>
        }
      />
      <div className="flex flex-wrap items-center gap-4">
        <Avatar className="h-16 w-16 border border-white/10">
          <AvatarImage src={profile.avatar_url ?? undefined} alt={displayName} />
          <AvatarFallback>{initials || 'AA'}</AvatarFallback>
        </Avatar>
        <div className="space-y-1">
          <p className="text-lg font-semibold text-foreground">{displayName}</p>
          <p className="text-sm text-foreground/70">{profile.email ?? 'No email on file'}</p>
          <p className="text-xs uppercase tracking-[0.3em] text-foreground/50">
            {profile.role ?? 'member'}
          </p>
        </div>
      </div>
    </GlassPanel>
  );
}
