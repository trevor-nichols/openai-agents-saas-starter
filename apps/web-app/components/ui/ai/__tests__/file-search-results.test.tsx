import { render, screen } from '@testing-library/react';

import { FileSearchResults } from '../file-search-results';

const sample = [
  {
    file_id: 'file-1',
    filename: 'notes.txt',
    score: 0.9876,
    vector_store_id: 'vs-123',
    text: 'First line of the document',
    attributes: { topic: 'demo' },
  },
  {
    file_id: 'file-2',
    filename: null,
    score: null,
    vector_store_id: null,
    text: null,
    attributes: {},
  },
];

describe('FileSearchResults', () => {
  it('renders filename, score badge, text snippet, and attributes', () => {
    render(<FileSearchResults results={sample} />);

    expect(screen.getByText('notes.txt')).toBeInTheDocument();
    expect(screen.getByText('(file-1)')).toBeInTheDocument();
    expect(screen.getByText(/Score 0\.988/)).toBeInTheDocument();
    expect(screen.getByText('VS: vs-123')).toBeInTheDocument();
    expect(screen.getByText('First line of the document')).toBeInTheDocument();
    expect(screen.getByText('topic')).toBeInTheDocument();
    expect(screen.getByText('demo')).toBeInTheDocument();
  });

  it('renders an empty state when no results are provided', () => {
    render(<FileSearchResults results={[]} />);
    expect(screen.getByText('No files matched this search.')).toBeInTheDocument();
  });
});
