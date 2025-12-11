import type { Meta, StoryObj } from '@storybook/react';
import { Toaster } from '../sonner';
import { toast } from 'sonner';
import { Button } from '../button';

const meta: Meta<typeof Toaster> = {
  title: 'UI/Feedback/Sonner',
  component: Toaster,
  tags: ['autodocs'],
  parameters: {
    layout: 'centered',
  },
  decorators: [
    (Story) => (
      <>
        <Story />
        <Toaster />
      </>
    ),
  ],
};

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  render: () => (
    <Button onClick={() => toast('This is a default toast')}>
      Show Default Toast
    </Button>
  ),
};

export const Success: Story = {
  render: () => (
    <Button onClick={() => toast.success('Your changes have been saved')}>
      Show Success Toast
    </Button>
  ),
};

export const Error: Story = {
  render: () => (
    <Button
      variant="destructive"
      onClick={() => toast.error('Something went wrong. Please try again.')}
    >
      Show Error Toast
    </Button>
  ),
};

export const Warning: Story = {
  render: () => (
    <Button
      variant="outline"
      onClick={() => toast.warning('Your session will expire in 5 minutes')}
    >
      Show Warning Toast
    </Button>
  ),
};

export const Info: Story = {
  render: () => (
    <Button onClick={() => toast.info('New features are available')}>
      Show Info Toast
    </Button>
  ),
};

export const WithDescription: Story = {
  render: () => (
    <Button
      onClick={() =>
        toast('Event created', {
          description: 'Your event has been created successfully',
        })
      }
    >
      Show Toast with Description
    </Button>
  ),
};

export const WithAction: Story = {
  render: () => (
    <Button
      onClick={() =>
        toast('File deleted', {
          action: {
            label: 'Undo',
            onClick: () => toast('Deletion undone'),
          },
        })
      }
    >
      Show Toast with Action
    </Button>
  ),
};

export const PromiseToast: Story = {
  render: () => {
    const promise = (): Promise<{ name: string }> =>
      new Promise((resolve) => setTimeout(() => resolve({ name: 'User' }), 2000));

    return (
      <Button
        onClick={() =>
          toast.promise(promise(), {
            loading: 'Loading...',
            success: (data) => `${data.name} has been loaded`,
            error: 'Error loading data',
          })
        }
      >
        Show Promise Toast
      </Button>
    );
  },
};

export const CustomDuration: Story = {
  render: () => (
    <Button onClick={() => toast('This will last 10 seconds', { duration: 10000 })}>
      Show Long Toast (10s)
    </Button>
  ),
};

export const Loading: Story = {
  render: () => (
    <Button onClick={() => toast.loading('Loading your data...')}>
      Show Loading Toast
    </Button>
  ),
};

export const AllTypes: Story = {
  render: () => (
    <div className="flex flex-wrap gap-2">
      <Button onClick={() => toast('Default toast')}>Default</Button>
      <Button onClick={() => toast.success('Success toast')}>Success</Button>
      <Button onClick={() => toast.error('Error toast')}>Error</Button>
      <Button onClick={() => toast.warning('Warning toast')}>Warning</Button>
      <Button onClick={() => toast.info('Info toast')}>Info</Button>
      <Button onClick={() => toast.loading('Loading...')}>Loading</Button>
    </div>
  ),
};

export const WithCloseButton: Story = {
  render: () => (
    <Button
      onClick={() =>
        toast('You can close this manually', {
          duration: Infinity,
          closeButton: true,
        })
      }
    >
      Show Dismissible Toast
    </Button>
  ),
};

export const Position: Story = {
  render: () => (
    <div className="flex flex-wrap gap-2">
      <Button onClick={() => toast('Top Left', { position: 'top-left' })}>
        Top Left
      </Button>
      <Button onClick={() => toast('Top Center', { position: 'top-center' })}>
        Top Center
      </Button>
      <Button onClick={() => toast('Top Right', { position: 'top-right' })}>
        Top Right
      </Button>
      <Button onClick={() => toast('Bottom Left', { position: 'bottom-left' })}>
        Bottom Left
      </Button>
      <Button onClick={() => toast('Bottom Center', { position: 'bottom-center' })}>
        Bottom Center
      </Button>
      <Button onClick={() => toast('Bottom Right', { position: 'bottom-right' })}>
        Bottom Right
      </Button>
    </div>
  ),
};
