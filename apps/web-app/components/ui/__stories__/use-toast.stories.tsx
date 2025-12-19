import type { Meta, StoryObj } from '@storybook/react';
import { Button } from '../button';
import { useToast } from '../use-toast';

const meta: Meta = {
  title: 'UI/Feedback/Toasts',
};

export default meta;

type Story = StoryObj<typeof meta>;

const ToastDemo = () => {
  const toast = useToast();
  return (
    <div className="flex flex-wrap gap-3">
      <Button size="sm" onClick={() => toast.success({ title: 'Workspace created' })}>
        Success
      </Button>
      <Button size="sm" onClick={() => toast.error({ title: 'Billing failed', description: 'Card declined' })}>
        Error
      </Button>
      <Button size="sm" onClick={() => toast.info({ title: 'Scheduled for later' })}>
        Info
      </Button>
    </div>
  );
};

export const Default: Story = {
  render: () => <ToastDemo />,
};
