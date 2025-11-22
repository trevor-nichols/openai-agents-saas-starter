import type { Meta, StoryObj } from '@storybook/react';

import {
  CodeBlock,
  CodeBlockBody,
  CodeBlockContent,
  CodeBlockCopyButton,
  CodeBlockFiles,
  CodeBlockHeader,
  CodeBlockItem,
  CodeBlockSelect,
  CodeBlockSelectContent,
  CodeBlockSelectItem,
  CodeBlockSelectTrigger,
  CodeBlockSelectValue,
} from './index';

const sampleCode = [
  {
    language: 'typescript',
    filename: 'agent.ts',
    code: `import { Agent } from '@openai/agents'\n\nexport const supportAgent = new Agent({\n  name: 'Support Concierge',\n  model: 'gpt-5.1',\n  tools: ['retrieval', 'browser'],\n})`,
  },
  {
    language: 'bash',
    filename: 'deploy.sh',
    code: `pnpm install\npnpm lint\npnpm type-check\npnpm storybook:build`,
  },
];

const meta: Meta<typeof CodeBlock> = {
  title: 'UI/Data/CodeBlock',
  component: CodeBlock,
  tags: ['autodocs'],
  args: {
    data: sampleCode,
    defaultValue: sampleCode[0]?.language,
  },
};

export default meta;

type Story = StoryObj<typeof CodeBlock>;

export const Default: Story = {
  render: (args) => (
    <CodeBlock {...args} className="max-w-3xl">
      <CodeBlockHeader>
        <CodeBlockFiles>{(item) => <CodeBlockItem key={item.filename} value={item.language}>{item.filename}</CodeBlockItem>}</CodeBlockFiles>
        <div className="flex items-center gap-2">
          <CodeBlockSelect>
            <CodeBlockSelectTrigger aria-label="Select file">
              <CodeBlockSelectValue placeholder="Select file" />
            </CodeBlockSelectTrigger>
            <CodeBlockSelectContent>
              {(item) => (
                <CodeBlockSelectItem key={item.filename} value={item.language}>
                  {item.filename}
                </CodeBlockSelectItem>
              )}
            </CodeBlockSelectContent>
          </CodeBlockSelect>
          <CodeBlockCopyButton />
        </div>
      </CodeBlockHeader>
      <CodeBlockBody className="max-h-[360px]">
        {(item) => <CodeBlockContent language={item.language}>{item.code}</CodeBlockContent>}
      </CodeBlockBody>
    </CodeBlock>
  ),
};
