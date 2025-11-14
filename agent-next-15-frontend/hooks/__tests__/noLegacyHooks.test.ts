import { describe, it, expect } from 'vitest';
import { readdirSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const FORBIDDEN_HOOK_FILES = new Set(['useBillingStream.ts', 'useSilentRefresh.ts']);

describe('Legacy hook guard', () => {
  it('prevents reintroducing removed streaming hooks in hooks/', () => {
    const hooksDir = join(__dirname, '..');
    const entries = readdirSync(hooksDir);
    const offenders = entries.filter((entry) => FORBIDDEN_HOOK_FILES.has(entry));
    expect(offenders).toEqual([]);
  });
});
