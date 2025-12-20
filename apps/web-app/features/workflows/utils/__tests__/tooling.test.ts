import { describe, expect, it } from 'vitest';

import { resolveSupportsContainers, resolveSupportsFileSearch } from '../tooling';

describe('workflow tooling helpers', () => {
  it('detects code interpreter support', () => {
    expect(resolveSupportsContainers(['code_interpreter'])).toBe(true);
    expect(resolveSupportsContainers(['file_search'])).toBe(false);
  });

  it('detects file_search support', () => {
    expect(resolveSupportsFileSearch(['file_search'])).toBe(true);
    expect(resolveSupportsFileSearch(['code_interpreter'])).toBe(false);
  });
});
