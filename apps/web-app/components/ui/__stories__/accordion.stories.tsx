import type { Meta, StoryObj } from '@storybook/react';

import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '../accordion';

const meta: Meta<typeof Accordion> = {
  title: 'UI/Surfaces/Accordion',
  component: Accordion,
  tags: ['autodocs'],
};

export default meta;

type Story = StoryObj<typeof Accordion>;

const items = [
  { value: 'item-1', title: 'What is an Agent?', body: 'Agents are tools that combine reasoning with tool use and memory.' },
  { value: 'item-2', title: 'Do you support streaming?', body: 'Yes, responses stream via Server Actions and SSE fallbacks.' },
  { value: 'item-3', title: 'How do I add tools?', body: 'Register tools in the FastAPI registry and map to UI affordances.' },
];

export const Default: Story = {
  render: () => (
    <Accordion type="single" collapsible className="w-full max-w-2xl">
      {items.map((item) => (
        <AccordionItem key={item.value} value={item.value}>
          <AccordionTrigger>{item.title}</AccordionTrigger>
          <AccordionContent>{item.body}</AccordionContent>
        </AccordionItem>
      ))}
    </Accordion>
  ),
};
