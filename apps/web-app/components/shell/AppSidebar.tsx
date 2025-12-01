'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Command } from 'lucide-react';

import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarRail,
} from '@/components/ui/sidebar';
import { SidebarUserMenu } from './SidebarUserMenu';
import type { AppNavItem } from './AppNavLinks';

interface AppSidebarProps extends React.ComponentProps<typeof Sidebar> {
  navItems: AppNavItem[];
  accountItems: AppNavItem[];
  user: {
    name?: string | null;
    email?: string | null;
    avatarUrl?: string | null;
    tenantId?: string | null;
  };
  brandHref?: string;
  brandLabel?: string;
}

export function AppSidebar({
  navItems,
  accountItems,
  user,
  brandHref = '/dashboard',
  brandLabel = 'Acme',
  ...props
}: AppSidebarProps) {
  const pathname = usePathname();

  return (
    <Sidebar collapsible="icon" {...props}>
      <SidebarHeader>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton size="lg" asChild>
              <Link href={brandHref}>
                <div className="flex aspect-square size-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
                  <Command className="size-4" />
                </div>
                <div className="grid flex-1 text-left text-sm leading-tight">
                  <span className="truncate font-semibold">{brandLabel}</span>
                  <span className="truncate text-xs">Enterprise</span>
                </div>
              </Link>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Platform</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {navItems.map((item) => (
                <SidebarMenuItem key={item.href}>
                  <SidebarMenuButton asChild isActive={pathname === item.href || (item.href !== '/' && pathname.startsWith(`${item.href}/`))} tooltip={item.label}>
                    <Link href={item.href}>
                      {item.icon && <item.icon />}
                      <span>{item.label}</span>
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
        
        {accountItems.length > 0 && (
             <SidebarGroup className="mt-auto">
                <SidebarGroupLabel>Account</SidebarGroupLabel>
                <SidebarGroupContent>
                    <SidebarMenu>
                    {accountItems.map((item) => (
                        <SidebarMenuItem key={item.href}>
                        <SidebarMenuButton asChild isActive={pathname === item.href} tooltip={item.label}>
                            <Link href={item.href}>
                            {item.icon && <item.icon />}
                            <span>{item.label}</span>
                            </Link>
                        </SidebarMenuButton>
                        </SidebarMenuItem>
                    ))}
                    </SidebarMenu>
                </SidebarGroupContent>
            </SidebarGroup>
        )}
      </SidebarContent>
      <SidebarFooter>
        <SidebarUserMenu
            userName={user.name}
            userEmail={user.email}
            tenantId={user.tenantId}
            avatarUrl={user.avatarUrl}
        />
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  );
}