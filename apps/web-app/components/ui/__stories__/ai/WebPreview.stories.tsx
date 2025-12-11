import type { Meta, StoryObj } from '@storybook/react';
import { ArrowLeft, ArrowRight, RotateCcw } from 'lucide-react';

import {
  WebPreview,
  WebPreviewBody,
  WebPreviewConsole,
  WebPreviewNavigation,
  WebPreviewNavigationButton,
  WebPreviewUrl,
} from '../../ai/web-preview';

const meta: Meta<typeof WebPreview> = {
  title: 'AI/WebPreview',
  component: WebPreview,
  tags: ['autodocs'],
  parameters: {
    layout: 'fullscreen',
  },
};

export default meta;

type Story = StoryObj<typeof WebPreview>;

const logs = [
  { level: 'log' as const, message: 'Loaded page', timestamp: new Date() },
  { level: 'warn' as const, message: 'Mixed content blocked', timestamp: new Date() },
];

export const Default: Story = {
  render: () => (
    <div className="h-[420px] w-full">
      <WebPreview defaultUrl="https://example.com" className="h-full">
        <WebPreviewNavigation>
          <WebPreviewNavigationButton tooltip="Back">
            <ArrowLeft className="h-4 w-4" />
          </WebPreviewNavigationButton>
          <WebPreviewNavigationButton tooltip="Forward">
            <ArrowRight className="h-4 w-4" />
          </WebPreviewNavigationButton>
          <WebPreviewNavigationButton tooltip="Reload">
            <RotateCcw className="h-4 w-4" />
          </WebPreviewNavigationButton>
          <WebPreviewUrl />
        </WebPreviewNavigation>
        <WebPreviewBody />
        <WebPreviewConsole logs={logs} />
      </WebPreview>
    </div>
  ),
};
