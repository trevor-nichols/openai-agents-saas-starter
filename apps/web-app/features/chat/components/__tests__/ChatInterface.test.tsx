import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';

import { renderToolOutput } from '@/components/ui/ai/renderToolOutput';
import type { ImageGenerationCall } from '@/lib/api/client/types.gen';
import type { FileSearchResult } from '@/lib/api/client/types.gen';

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
    const frames: ImageGenerationCall[] = [
      {
        id: 'img-1',
        type: 'image_generation_call',
        status: 'completed',
        result: 'data:image/png;base64,aGVsbG8=',
        format: 'png',
      },
    ];

    render(<div>{renderToolOutput({ output: frames })}</div>);

    const img = screen.getByRole('img');
    expect(img).toBeInTheDocument();
    expect(img.getAttribute('src')).toContain('data:image/png;base64');
  });
});
