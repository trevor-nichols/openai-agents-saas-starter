import type { Meta, StoryObj } from '@storybook/react';
import { Button } from './button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from './card';

const meta: Meta<typeof Card> = {
  title: 'UI/Layout/Card',
  component: Card,
  tags: ['autodocs'],
};

export default meta;

type Story = StoryObj<typeof Card>;

export const Basic: Story = {
  args: {
    children: (
      <>
        <CardHeader>
          <CardTitle>Project Aurora</CardTitle>
          <CardDescription>LLM-powered support copilot for enterprise customers.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-2 text-sm text-foreground/80">
          <p>• 18 active workspaces</p>
          <p>• 142k monthly queries</p>
          <p>• Latency p95: 420ms</p>
        </CardContent>
        <CardFooter className="justify-end gap-2">
          <Button variant="outline" size="sm">
            Docs
          </Button>
          <Button size="sm">Open</Button>
        </CardFooter>
      </>
    ),
  },
};

export const WithMutedBackground: Story = {
  args: {
    className: 'bg-muted/40',
    children: (
      <CardHeader>
        <CardTitle>Muted Card</CardTitle>
        <CardDescription>Use muted backgrounds for nested cards.</CardDescription>
      </CardHeader>
    ),
  },
};
