import type { Meta, StoryObj } from '@storybook/react';

import { CodeBlock, CodeBlockCopyButton } from './code-block';

const meta: Meta<typeof CodeBlock> = {
  title: 'AI/CodeBlock',
  component: CodeBlock,
  tags: ['autodocs'],
};

export default meta;

type Story = StoryObj<typeof CodeBlock>;

const sample = `async function getUsage() {
  const res = await fetch('/api/usage');
  return res.json();
}

await getUsage();`;

export const Default: Story = {
  render: () => (
    <CodeBlock code={sample} language="typescript" showLineNumbers>
      <CodeBlockCopyButton aria-label="Copy code" />
    </CodeBlock>
  ),
};
