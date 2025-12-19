import type { Meta, StoryObj } from '@storybook/react';
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupAction,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarInset,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarProvider,
  SidebarRail,
  SidebarTrigger,
} from '../sidebar';
import {
  Calendar,
  ChevronRight,
  Home,
  Inbox,
  MoreHorizontal,
  Plus,
  Search,
  Settings,
  User,
} from 'lucide-react';
import { Avatar, AvatarFallback, AvatarImage } from '../avatar';
import { Separator } from '../separator';

const meta: Meta<typeof Sidebar> = {
  title: 'UI/Shell/Sidebar',
  component: Sidebar,
  parameters: {
    layout: 'fullscreen',
  },
  decorators: [
    (Story) => (
      <div className="min-h-screen w-full bg-background text-foreground">
        <SidebarProvider>
           <Story />
        </SidebarProvider>
      </div>
    ),
  ],
};

export default meta;
type Story = StoryObj<typeof Sidebar>;

export const Simple: Story = {
  render: () => (
    <>
      <Sidebar>
        <SidebarContent>
          <SidebarGroup>
            <SidebarGroupLabel>Application</SidebarGroupLabel>
            <SidebarGroupContent>
              <SidebarMenu>
                {[
                  { title: 'Home', icon: Home, url: '#' },
                  { title: 'Inbox', icon: Inbox, url: '#' },
                  { title: 'Calendar', icon: Calendar, url: '#' },
                  { title: 'Search', icon: Search, url: '#' },
                  { title: 'Settings', icon: Settings, url: '#' },
                ].map((item) => (
                  <SidebarMenuItem key={item.title}>
                    <SidebarMenuButton asChild>
                      <a href={item.url}>
                        <item.icon />
                        <span>{item.title}</span>
                      </a>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                ))}
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>
        </SidebarContent>
        <SidebarFooter>
            <SidebarMenu>
              <SidebarMenuItem>
                <SidebarMenuButton>
                   <User />
                   <span>User Profile</span>
                </SidebarMenuButton>
              </SidebarMenuItem>
            </SidebarMenu>
        </SidebarFooter>
      </Sidebar>
      <SidebarInset>
        <header className="flex h-14 items-center border-b px-4 gap-2">
          <SidebarTrigger />
          <Separator orientation="vertical" className="h-4" />
          <span className="font-medium">Application</span>
        </header>
        <div className="p-4">
          <div className="rounded-lg border border-dashed p-8 text-center text-muted-foreground">
            Main content goes here
          </div>
        </div>
      </SidebarInset>
    </>
  ),
};

export const Collapsible: Story = {
    args: {
        collapsible: "icon"
    },
    render: (args) => (
      <>
        <Sidebar {...args}>
          <SidebarHeader>
              <div className="flex items-center gap-2 px-2 py-1">
                 <div className="size-6 rounded bg-primary"></div>
                 <span className="font-bold">Acme Inc</span>
              </div>
          </SidebarHeader>
          <SidebarContent>
            <SidebarGroup>
              <SidebarGroupLabel>Platform</SidebarGroupLabel>
              <SidebarGroupContent>
                <SidebarMenu>
                  {[
                    { title: 'Dashboard', icon: Home },
                    { title: 'Analytics', icon: Inbox },
                    { title: 'Team', icon: User },
                  ].map((item) => (
                    <SidebarMenuItem key={item.title}>
                      <SidebarMenuButton tooltip={item.title}>
                          <item.icon />
                          <span>{item.title}</span>
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                  ))}
                </SidebarMenu>
              </SidebarGroupContent>
            </SidebarGroup>
             <SidebarGroup>
              <SidebarGroupLabel>Projects</SidebarGroupLabel>
              <SidebarGroupAction title="Add Project">
                  <Plus /> <span className="sr-only">Add Project</span>
              </SidebarGroupAction>
              <SidebarGroupContent>
                <SidebarMenu>
                  {[
                    { title: 'Design System', icon: ChevronRight },
                    { title: 'Marketing Site', icon: ChevronRight },
                    { title: 'Mobile App', icon: ChevronRight },
                  ].map((item) => (
                    <SidebarMenuItem key={item.title}>
                      <SidebarMenuButton>
                          <span className="truncate">{item.title}</span>
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                  ))}
                </SidebarMenu>
              </SidebarGroupContent>
            </SidebarGroup>
          </SidebarContent>
          <SidebarFooter>
             <div className="p-2">
                 <div className="flex items-center gap-2 rounded-md bg-sidebar-accent p-2 text-sm">
                    <Avatar className="size-8 rounded">
                        <AvatarImage src="https://github.com/shadcn.png" />
                        <AvatarFallback>CN</AvatarFallback>
                    </Avatar>
                    <div className="grid flex-1 text-left text-xs leading-tight">
                      <span className="truncate font-semibold">Shadcn</span>
                      <span className="truncate text-xs">m@example.com</span>
                    </div>
                    <MoreHorizontal className="size-4" />
                 </div>
             </div>
          </SidebarFooter>
          <SidebarRail />
        </Sidebar>
        <SidebarInset>
          <header className="flex h-14 items-center border-b px-4 gap-2">
            <SidebarTrigger />
            <Separator orientation="vertical" className="h-4" />
            <span className="font-medium">Dashboard</span>
          </header>
          <div className="p-4 space-y-4">
            <div className="grid grid-cols-3 gap-4">
                <div className="aspect-video rounded-xl bg-muted/50" />
                <div className="aspect-video rounded-xl bg-muted/50" />
                <div className="aspect-video rounded-xl bg-muted/50" />
            </div>
             <div className="min-h-[100vh] rounded-xl bg-muted/50" />
          </div>
        </SidebarInset>
      </>
    ),
  };
