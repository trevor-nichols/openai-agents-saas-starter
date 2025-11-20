'use client';

import { useState } from 'react';
import { Menu } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from '@/components/ui/sheet';

import { AppNavLinks, type AppNavItem } from './AppNavLinks';

interface AppMobileNavProps {
  navItems: AppNavItem[];
  accountItems: AppNavItem[];
}

export function AppMobileNav({ navItems, accountItems }: AppMobileNavProps) {
  const [open, setOpen] = useState(false);

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <Button
          variant="outline"
          size="sm"
          className="inline-flex items-center gap-2 rounded-full border-white/15 bg-white/5 text-sm font-medium text-foreground/80 hover:bg-white/10"
        >
          <Menu className="h-4 w-4" aria-hidden />
          Menu
        </Button>
      </SheetTrigger>
      <SheetContent side="left" className="w-full max-w-sm border-white/10 bg-background/95 text-foreground">
        <SheetHeader>
          <SheetTitle>Navigation</SheetTitle>
        </SheetHeader>

        <div className="mt-6 space-y-6">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.3em] text-foreground/50">Primary</p>
            <AppNavLinks items={navItems} variant="mobile" onNavigate={() => setOpen(false)} className="mt-2" />
          </div>

          <Separator className="bg-white/10" />

          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.3em] text-foreground/50">Account</p>
            <AppNavLinks
              items={accountItems}
              variant="mobile"
              onNavigate={() => setOpen(false)}
              className="mt-2"
            />
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}
