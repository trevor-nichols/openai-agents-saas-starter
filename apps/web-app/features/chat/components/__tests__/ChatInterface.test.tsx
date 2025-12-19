import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';

import { renderToolOutput } from '@/components/ui/ai/renderToolOutput';
import type { FileSearchResult } from '@/lib/api/client/types.gen';
import type { GeneratedImageFrame } from '@/lib/streams/imageFrames';

describe('renderToolOutput helper', () => {
  it('renders file search results with the custom renderer', () => {
    const output: FileSearchResult[] = [
      {
        file_id: 'file-1',
        filename: 'report.pdf',
        score: 0.9,
        vector_store_id: 'vs-1',
        text: 'Quarterly summary',
      },
    ];

    render(<div>{renderToolOutput({ output })}</div>);

    expect(screen.getByText('report.pdf')).toBeInTheDocument();
    expect(screen.getByText('(file-1)')).toBeInTheDocument();
    expect(screen.getByText(/Score 0\.900/)).toBeInTheDocument();
  });

  it('renders image generation frames with the AI image component', () => {
    const frames: GeneratedImageFrame[] = [
      {
        id: 'img-1',
        status: 'completed',
        src: 'data:image/png;base64,aGVsbG8=',
      },
    ];

    render(<div>{renderToolOutput({ output: frames })}</div>);

    const img = screen.getByRole('img');
    expect(img).toBeInTheDocument();
    expect(img.getAttribute('src')).toContain('data:image/png;base64');
  });
});
