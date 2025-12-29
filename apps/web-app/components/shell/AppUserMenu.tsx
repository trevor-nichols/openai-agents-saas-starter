'use client';

import Link from 'next/link';
import { useTransition } from 'react';

import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { apiV1Path } from '@/lib/apiPaths';

interface AppUserMenuProps {
  userName?: string | null;
  userEmail?: string | null;
  tenantId?: string | null;
  avatarUrl?: string | null;
}

export function AppUserMenu({ userName, userEmail, tenantId, avatarUrl }: AppUserMenuProps) {
  const [isPending, startTransition] = useTransition();

  const displayName = userName ?? userEmail ?? 'Signed in user';
  const displayEmail = userName ? (userEmail ?? tenantId ?? 'Account') : 'Account';
  const initials = displayName
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0])
    .join('')
    .toUpperCase() || 'U';

  const handleLogout = () => {
    startTransition(async () => {
      try {
        await fetch(apiV1Path('/auth/logout'), { method: 'POST', cache: 'no-store' });
      } catch (error) {
        console.error('[auth] Logout request failed', error);
      } finally {
        window.location.href = '/login';
      }
    });
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          className="h-10 gap-2 rounded-full border border-white/10 bg-white/5 px-3 text-sm font-medium text-foreground/80 hover:bg-white/10"
        >
          <Avatar className="h-7 w-7">
            <AvatarImage src={avatarUrl ?? undefined} alt={displayName} />
            <AvatarFallback className="text-xs">{initials}</AvatarFallback>
          </Avatar>
          <span className="hidden sm:inline">{displayName}</span>
        </Button>
      </DropdownMenuTrigger>

      <DropdownMenuContent align="end" className="w-56">
        <DropdownMenuLabel className="flex flex-col space-y-1">
          <span className="text-sm font-semibold">{displayName}</span>
          <span className="text-xs text-muted-foreground">{displayEmail}</span>
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem asChild>
          <Link href="/account">Profile</Link>
        </DropdownMenuItem>
        <DropdownMenuItem asChild>
          <Link href="/settings/team">Settings</Link>
        </DropdownMenuItem>
        <DropdownMenuItem asChild>
          <Link href="/billing">Billing</Link>
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem onClick={handleLogout} disabled={isPending}>
          {isPending ? 'Signing out…' : 'Log out'}
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
