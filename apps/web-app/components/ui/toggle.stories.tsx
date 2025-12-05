import type { Meta, StoryObj } from '@storybook/react';
import { Toggle } from './toggle';
import { Bold, Italic, Underline, AlignLeft, AlignCenter, AlignRight } from 'lucide-react';

const meta: Meta<typeof Toggle> = {
  title: 'UI/Inputs/Toggle',
  component: Toggle,
  tags: ['autodocs'],
  argTypes: {
    variant: {
      control: 'select',
      options: ['default', 'outline'],
      description: 'The visual style of the toggle',
    },
    size: {
      control: 'select',
      options: ['default', 'sm', 'lg'],
      description: 'The size of the toggle',
    },
    disabled: {
      control: 'boolean',
      description: 'Whether the toggle is disabled',
    },
  },
  parameters: {
    layout: 'centered',
  },
};

export default meta;
type Story = StoryObj<typeof Toggle>;

export const Default: Story = {
  args: {
    children: 'Toggle',
  },
};

export const Outline: Story = {
  args: {
    children: 'Toggle',
    variant: 'outline',
  },
};

export const Disabled: Story = {
  args: {
    children: 'Disabled',
    disabled: true,
  },
};

export const WithIcon: Story = {
  render: () => (
    <div className="flex items-center gap-2">
      <Toggle aria-label="Toggle bold">
        <Bold className="h-4 w-4" />
      </Toggle>
      <Toggle aria-label="Toggle italic">
        <Italic className="h-4 w-4" />
      </Toggle>
      <Toggle aria-label="Toggle underline">
        <Underline className="h-4 w-4" />
      </Toggle>
    </div>
  ),
};

export const WithIconAndText: Story = {
  render: () => (
    <div className="flex items-center gap-2">
      <Toggle aria-label="Toggle bold">
        <Bold className="h-4 w-4 mr-2" />
        Bold
      </Toggle>
      <Toggle aria-label="Toggle italic">
        <Italic className="h-4 w-4 mr-2" />
        Italic
      </Toggle>
    </div>
  ),
};

export const Sizes: Story = {
  render: () => (
    <div className="flex items-center gap-2">
      <Toggle size="sm" aria-label="Small toggle">
        <Bold className="h-4 w-4" />
      </Toggle>
      <Toggle size="default" aria-label="Default toggle">
        <Bold className="h-4 w-4" />
      </Toggle>
      <Toggle size="lg" aria-label="Large toggle">
        <Bold className="h-4 w-4" />
      </Toggle>
    </div>
  ),
};

export const Variants: Story = {
  render: () => (
    <div className="flex items-center gap-2">
      <Toggle variant="default" aria-label="Default variant">
        <Bold className="h-4 w-4" />
      </Toggle>
      <Toggle variant="outline" aria-label="Outline variant">
        <Bold className="h-4 w-4" />
      </Toggle>
    </div>
  ),
};

export const TextFormatting: Story = {
  render: () => (
    <div className="flex items-center gap-1">
      <Toggle aria-label="Toggle bold" defaultPressed>
        <Bold className="h-4 w-4" />
      </Toggle>
      <Toggle aria-label="Toggle italic">
        <Italic className="h-4 w-4" />
      </Toggle>
      <Toggle aria-label="Toggle underline">
        <Underline className="h-4 w-4" />
      </Toggle>
      <div className="w-px h-6 bg-border mx-1" />
      <Toggle aria-label="Align left" defaultPressed>
        <AlignLeft className="h-4 w-4" />
      </Toggle>
      <Toggle aria-label="Align center">
        <AlignCenter className="h-4 w-4" />
      </Toggle>
      <Toggle aria-label="Align right">
        <AlignRight className="h-4 w-4" />
      </Toggle>
    </div>
  ),
};

export const OutlineGroup: Story = {
  render: () => (
    <div className="flex items-center gap-1">
      <Toggle variant="outline" aria-label="Toggle bold">
        <Bold className="h-4 w-4" />
      </Toggle>
      <Toggle variant="outline" aria-label="Toggle italic">
        <Italic className="h-4 w-4" />
      </Toggle>
      <Toggle variant="outline" aria-label="Toggle underline">
        <Underline className="h-4 w-4" />
      </Toggle>
    </div>
  ),
};

export const SmallGroup: Story = {
  render: () => (
    <div className="flex items-center gap-1">
      <Toggle size="sm" aria-label="Toggle bold">
        <Bold className="h-4 w-4" />
      </Toggle>
      <Toggle size="sm" aria-label="Toggle italic">
        <Italic className="h-4 w-4" />
      </Toggle>
      <Toggle size="sm" aria-label="Toggle underline">
        <Underline className="h-4 w-4" />
      </Toggle>
    </div>
  ),
};

export const LargeGroup: Story = {
  render: () => (
    <div className="flex items-center gap-1">
      <Toggle size="lg" aria-label="Toggle bold">
        <Bold className="h-4 w-4" />
      </Toggle>
      <Toggle size="lg" aria-label="Toggle italic">
        <Italic className="h-4 w-4" />
      </Toggle>
      <Toggle size="lg" aria-label="Toggle underline">
        <Underline className="h-4 w-4" />
      </Toggle>
    </div>
  ),
};
