import type { Meta, StoryObj } from '@storybook/react';
import { FileSearch, SearchX, Home } from 'lucide-react';
import { Button } from '@/components/ui/button';

import { EmptyState } from '../../states/EmptyState';
import { ErrorState } from '../../states/ErrorState';
import { SkeletonPanel } from '../../states/SkeletonPanel';

const meta: Meta = {
  title: 'UI/States',
  parameters: {
    layout: 'padded',
  },
};

export default meta;
type Story = StoryObj;

export const Empty: Story = {
  render: () => (
    <div className="max-w-md mx-auto">
      <EmptyState
        title="No documents found"
        description="Get started by creating a new document or importing one from your computer."
        icon={<FileSearch className="h-6 w-6" />}
        action={<Button>Create Document</Button>}
      />
    </div>
  ),
};

export const EmptySimple: Story = {
  render: () => (
    <div className="max-w-md mx-auto">
      <EmptyState
        title="No results"
        description="Try adjusting your search filters to find what you're looking for."
        icon={<SearchX className="h-6 w-6" />}
      />
    </div>
  ),
};

export const Error: Story = {
  render: () => (
    <div className="max-w-md mx-auto">
      <ErrorState
        title="Failed to load dashboard"
        message="We encountered an unexpected error while fetching your dashboard data. Please check your connection and try again."
        onRetry={() => alert('Retrying...')}
      />
    </div>
  ),
};

export const ErrorCustomAction: Story = {
  render: () => (
    <div className="max-w-md mx-auto">
      <ErrorState
        title="Access Denied"
        message="You don't have permission to view this resource."
        action={
          <div className="flex gap-3">
             <Button variant="outline" onClick={() => alert('Go Home')}>
              <Home className="mr-2 h-4 w-4" /> Go Home
            </Button>
            <Button onClick={() => alert('Request Access')}>Request Access</Button>
          </div>
        }
      />
    </div>
  ),
};

export const Skeleton: Story = {
  render: () => (
    <div className="max-w-md mx-auto">
      <SkeletonPanel lines={3} />
    </div>
  ),
};

export const SkeletonCustom: Story = {
  render: () => (
    <div className="max-w-md mx-auto">
      <SkeletonPanel className="p-8" lines={6} />
    </div>
  ),
};

