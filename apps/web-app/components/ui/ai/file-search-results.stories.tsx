import type { Meta, StoryObj } from '@storybook/react';
import type { FileSearchResult } from '@/lib/api/client/types.gen';

import { FileSearchResults } from './file-search-results';

const meta: Meta<typeof FileSearchResults> = {
  title: 'AI/FileSearchResults',
  component: FileSearchResults,
  tags: ['autodocs'],
};

export default meta;

type Story = StoryObj<typeof FileSearchResults>;

const mockResults: FileSearchResult[] = [
  {
    file_id: 'file-abc123',
    filename: 'product-requirements.pdf',
    vector_store_id: 'vs-xyz789',
    score: 0.945,
    text: 'The user authentication system must support OAuth 2.0, SAML, and traditional username/password login methods. All sessions should expire after 24 hours of inactivity.',
  },
  {
    file_id: 'file-def456',
    filename: 'architecture-diagram.png',
    vector_store_id: 'vs-xyz789',
    score: 0.892,
    text: 'System architecture showing microservices communication patterns, API gateway, and event-driven data flow between services.',
    attributes: {
      'Created By': 'Engineering Team',
      'Last Modified': '2025-11-28',
      'Document Type': 'Diagram',
    },
  },
  {
    file_id: 'file-ghi789',
    filename: 'meeting-notes-q4.md',
    vector_store_id: 'vs-abc123',
    score: 0.756,
    text: 'Key decisions: Prioritize performance optimization in Q4, allocate 30% of sprint capacity to technical debt, implement new monitoring dashboard by end of quarter.',
    attributes: {
      Quarter: 'Q4 2025',
      Team: 'Product & Engineering',
    },
  },
];

export const Default: Story = {
  args: {
    results: mockResults,
  },
};

export const WithoutScores: Story = {
  args: {
    results: mockResults.map(({ score: _score, ...rest }) => ({
      ...rest,
      score: null,
    })),
  },
};

export const WithoutVectorStoreIds: Story = {
  args: {
    results: mockResults.map(({ vector_store_id: _vector_store_id, ...rest }) => rest),
  },
};

export const WithoutText: Story = {
  args: {
    results: mockResults.map(({ text: _text, ...rest }) => ({
      ...rest,
      text: null,
    })),
  },
};

export const MinimalResults: Story = {
  args: {
    results: [
      {
        file_id: 'file-minimal-1',
        filename: 'document.txt',
      },
      {
        file_id: 'file-minimal-2',
        filename: 'notes.md',
      },
    ],
  },
};

export const SingleResult: Story = {
  args: {
    results: [mockResults[0]!],
  },
};

export const LongFilename: Story = {
  args: {
    results: [
      {
        file_id: 'file-long-1',
        filename: 'very-long-filename-that-might-cause-layout-issues-in-the-ui-component.pdf',
        vector_store_id: 'vs-test',
        score: 0.889,
        text: 'This is a test document with a very long filename to ensure the component handles text wrapping correctly.',
        attributes: {
          'File Size': '2.4 MB',
          Pages: '156',
        },
      },
    ],
  },
};

export const ManyAttributes: Story = {
  args: {
    results: [
      {
        file_id: 'file-attrs-1',
        filename: 'comprehensive-report.pdf',
        vector_store_id: 'vs-reports',
        score: 0.921,
        text: 'Comprehensive quarterly report with detailed analysis of performance metrics, market trends, and strategic recommendations.',
        attributes: {
          Author: 'Jane Smith',
          Department: 'Business Intelligence',
          'Created Date': '2025-11-15',
          'Last Modified': '2025-12-01',
          Version: '2.3',
          Status: 'Final',
          'Page Count': '87',
          'File Size': '4.2 MB',
        },
      },
    ],
  },
};

export const EmptyResults: Story = {
  args: {
    results: [],
  },
};

export const CustomClassName: Story = {
  args: {
    results: mockResults.slice(0, 2),
    className: 'max-w-2xl mx-auto p-4 bg-background/50 rounded-lg',
  },
};
