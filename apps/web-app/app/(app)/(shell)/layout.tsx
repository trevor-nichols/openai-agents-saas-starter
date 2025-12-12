// File Path: app/(app)/(shell)/layout.tsx
// Description: Dashboard-style shell chrome (header + padded scrolling main).

import { AppPageHeading } from '@/components/shell/AppPageHeading';
import { AppNotificationMenu } from '@/components/shell/AppNotificationMenu';
import { InfoMenu } from '@/components/ui/nav-bar';
import { Separator } from '@/components/ui/separator';
import { SidebarTrigger } from '@/components/ui/sidebar';

import { getAppShellLayoutModel } from '../_utils/getAppShellLayoutModel';

interface AppShellLayoutProps {
  children: React.ReactNode;
}

export default async function AppShellLayout({ children }: AppShellLayoutProps) {
  const { navItems, accountNav, subtitle } = await getAppShellLayoutModel();

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <header className="sticky top-0 z-30 flex shrink-0 items-center gap-2 border-b border-white/10 bg-background/80 px-4 py-4 backdrop-blur-glass transition-[width,height] ease-linear group-has-[[data-collapsible=icon]]/sidebar-wrapper:h-auto">
        <div className="flex items-center gap-2 self-start pt-1">
          <SidebarTrigger className="-ml-1" />
          <Separator orientation="vertical" className="mr-2 h-4" />
        </div>

        <div className="flex flex-1 flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <AppPageHeading
            navItems={navItems}
            accountItems={accountNav}
            subtitle={subtitle}
          />
          <div className="flex items-center gap-3 justify-end self-start sm:self-auto">
            <div className="hidden md:flex items-center gap-2">
              <InfoMenu />
              <AppNotificationMenu />
            </div>
          </div>
        </div>
      </header>

      <main className="relative min-h-0 flex-1 overflow-y-auto px-4 py-8 sm:px-6 lg:px-10">
        <div className="mx-auto w-full max-w-[1400px] space-y-8">{children}</div>
      </main>
    </div>
  );
}

