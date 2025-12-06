import type { Meta, StoryObj } from '@storybook/react';
import { Avatar, AvatarFallback, AvatarImage } from './Avatar';
import { AvatarGroup } from './AvatarGroup';
import { AnimatedTooltip } from './AnimatedTooltip';

const meta: Meta = {
  title: 'UI/Data Display/Avatar',
  parameters: {
    layout: 'centered',
  },
};

export default meta;

type Story = StoryObj;

export const Basic: Story = {
  render: () => (
    <div className="flex gap-4">
      <Avatar>
        <AvatarImage src="https://github.com/shadcn.png" alt="@shadcn" />
        <AvatarFallback>CN</AvatarFallback>
      </Avatar>
      <Avatar>
        <AvatarImage src="https://github.com/vercel.png" alt="@vercel" />
        <AvatarFallback>VC</AvatarFallback>
      </Avatar>
      <Avatar>
        <AvatarFallback>JD</AvatarFallback>
      </Avatar>
    </div>
  ),
};

export const Sizes: Story = {
  render: () => (
    <div className="flex items-end gap-4">
      <Avatar className="h-8 w-8">
        <AvatarImage src="https://github.com/shadcn.png" />
        <AvatarFallback>SM</AvatarFallback>
      </Avatar>
      <Avatar className="h-10 w-10">
        <AvatarImage src="https://github.com/shadcn.png" />
        <AvatarFallback>MD</AvatarFallback>
      </Avatar>
      <Avatar className="h-14 w-14">
        <AvatarImage src="https://github.com/shadcn.png" />
        <AvatarFallback>LG</AvatarFallback>
      </Avatar>
    </div>
  ),
};

export const GroupMotion: Story = {
  render: () => (
    <AvatarGroup variant="motion">
      <Avatar>
        <AvatarImage src="https://github.com/shadcn.png" />
        <AvatarFallback>CN</AvatarFallback>
      </Avatar>
      <Avatar>
        <AvatarImage src="https://github.com/vercel.png" />
        <AvatarFallback>VC</AvatarFallback>
      </Avatar>
      <Avatar>
        <AvatarImage src="https://github.com/nextjs.png" />
        <AvatarFallback>NX</AvatarFallback>
      </Avatar>
    </AvatarGroup>
  ),
};

export const GroupCSS: Story = {
  render: () => (
    <AvatarGroup variant="css">
      <Avatar>
        <AvatarImage src="https://github.com/shadcn.png" />
        <AvatarFallback>CN</AvatarFallback>
      </Avatar>
      <Avatar>
        <AvatarImage src="https://github.com/vercel.png" />
        <AvatarFallback>VC</AvatarFallback>
      </Avatar>
      <Avatar>
        <AvatarImage src="https://github.com/nextjs.png" />
        <AvatarFallback>NX</AvatarFallback>
      </Avatar>
    </AvatarGroup>
  ),
};

export const GroupStack: Story = {
  render: () => (
    <AvatarGroup variant="stack" animate size={48}>
      <Avatar>
        <AvatarImage src="https://github.com/shadcn.png" alt="shadcn" />
        <AvatarFallback>CN</AvatarFallback>
      </Avatar>
      <Avatar>
        <AvatarImage src="https://github.com/vercel.png" alt="vercel" />
        <AvatarFallback>VC</AvatarFallback>
      </Avatar>
      <Avatar>
        <AvatarImage src="https://github.com/nextjs.png" alt="nextjs" />
        <AvatarFallback>NX</AvatarFallback>
      </Avatar>
      <Avatar>
        <AvatarImage src="https://github.com/openai.png" alt="openai" />
        <AvatarFallback>AI</AvatarFallback>
      </Avatar>
    </AvatarGroup>
  ),
};

const people = [
  {
    id: 1,
    name: 'John Doe',
    designation: 'Software Engineer',
    image: 'https://images.unsplash.com/photo-1599566150163-29194dcaad36?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=3387&q=80',
  },
  {
    id: 2,
    name: 'Robert Johnson',
    designation: 'Product Manager',
    image: 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxzZWFyY2h8Mnx8YXZhdGFyfGVufDB8fDB8fHww&auto=format&fit=crop&w=800&q=60',
  },
  {
    id: 3,
    name: 'Jane Smith',
    designation: 'Data Scientist',
    image: 'https://images.unsplash.com/photo-1580489944761-15a19d654956?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxzZWFyY2h8NXx8YXZhdGFyfGVufDB8fDB8fHww&auto=format&fit=crop&w=800&q=60',
  },
  {
    id: 4,
    name: 'Emily Davis',
    designation: 'UX Designer',
    image: 'https://images.unsplash.com/photo-1438761681033-6461ffad8d80?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxzZWFyY2h8MTB8fGF2YXRhcnxlbnwwfHwwfHx8MA%3D%3D&auto=format&fit=crop&w=800&q=60',
  },
  {
    id: 5,
    name: 'Tyler Durden',
    designation: 'Soap Developer',
    image: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=3540&q=80',
  },
];

export const TooltipAvatar: Story = {
  render: () => (
    <div className="flex flex-row items-center justify-center mb-10 w-full">
      <AnimatedTooltip items={people} />
    </div>
  ),
};

