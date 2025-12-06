import { describe, expect, it } from 'vitest';

import { formatAttachmentSize, formatStructuredOutput } from '../formatters';

describe('formatAttachmentSize', () => {
  it('handles bytes, KB, and MB ranges', () => {
    expect(formatAttachmentSize(512)).toBe('512 B');
    expect(formatAttachmentSize(2048)).toBe('2.0 KB');
    expect(formatAttachmentSize(5 * 1024 * 1024)).toBe('5.0 MB');
  });
});

describe('formatStructuredOutput', () => {
  it('stringifies objects with indentation', () => {
    const result = formatStructuredOutput({ foo: 'bar' });
    expect(result).toContain('foo');
    expect(result).toContain('bar');
  });

  it('falls back to string for non-serializable values', () => {
    const circular: Record<string, unknown> = {};
    circular.self = circular;
    const result = formatStructuredOutput(circular);
    expect(result).toBe('[object Object]');
  });
});
