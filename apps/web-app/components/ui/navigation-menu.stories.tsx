import type { Meta, StoryObj } from '@storybook/react';

import {
  NavigationMenu,
  NavigationMenuContent,
  NavigationMenuItem,
  NavigationMenuLink,
  NavigationMenuList,
  NavigationMenuTrigger,
} from './navigation-menu';

const meta: Meta<typeof NavigationMenu> = {
  title: 'UI/Navigation/NavigationMenu',
  component: NavigationMenu,
  tags: ['autodocs'],
};

export default meta;

type Story = StoryObj<typeof NavigationMenu>;

export const Default: Story = {
  render: () => (
    <NavigationMenu className="mx-auto">
      <NavigationMenuList>
        <NavigationMenuItem>
          <NavigationMenuTrigger>Product</NavigationMenuTrigger>
          <NavigationMenuContent className="p-4">
            <ul className="grid w-[320px] gap-2 text-sm">
              <li>
                <NavigationMenuLink className="block rounded-md p-3 hover:bg-muted/60">
                  Chat Workspace
                  <p className="text-muted-foreground text-xs">Streaming UI for agent responses.</p>
                </NavigationMenuLink>
              </li>
              <li>
                <NavigationMenuLink className="block rounded-md p-3 hover:bg-muted/60">
                  Billing
                  <p className="text-muted-foreground text-xs">Plans, usage, invoices.</p>
                </NavigationMenuLink>
              </li>
              <li>
                <NavigationMenuLink className="block rounded-md p-3 hover:bg-muted/60">
                  Security
                  <p className="text-muted-foreground text-xs">SAML, SCIM, audit logs.</p>
                </NavigationMenuLink>
              </li>
            </ul>
          </NavigationMenuContent>
        </NavigationMenuItem>

        <NavigationMenuItem>
          <NavigationMenuTrigger>Docs</NavigationMenuTrigger>
          <NavigationMenuContent className="p-4">
            <ul className="grid w-[260px] gap-2 text-sm">
              <li>
                <NavigationMenuLink className="block rounded-md p-3 hover:bg-muted/60">API Reference</NavigationMenuLink>
              </li>
              <li>
                <NavigationMenuLink className="block rounded-md p-3 hover:bg-muted/60">Guides</NavigationMenuLink>
              </li>
              <li>
                <NavigationMenuLink className="block rounded-md p-3 hover:bg-muted/60">Changelog</NavigationMenuLink>
              </li>
            </ul>
          </NavigationMenuContent>
        </NavigationMenuItem>

        <NavigationMenuItem>
          <NavigationMenuLink className="block rounded-md px-3 py-2 text-sm font-medium hover:bg-muted/60">
            Pricing
          </NavigationMenuLink>
        </NavigationMenuItem>
      </NavigationMenuList>
    </NavigationMenu>
  ),
};
