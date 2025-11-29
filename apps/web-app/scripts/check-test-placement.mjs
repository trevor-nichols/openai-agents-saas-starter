#!/usr/bin/env node

// Enforce test file placement conventions:
// - Route tests: `route.test.ts[x]` live beside their `route.ts` files.
// - All other tests live under a sibling `__tests__/` directory.

import { readdir } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');

// Directories that are safe to ignore while walking.
const IGNORE_DIRS = new Set([
  'node_modules',
  '.next',
  '.storybook',
  'storybook-static',
  'test-results',
  'public',
  'coverage',
  'dist',
  'out',
  '.turbo',
  'tests', // e2e lives here and follows Playwright naming.
]);

const TEST_FILE_SUFFIXES = ['.test.ts', '.test.tsx', '.spec.ts', '.spec.tsx'];

const isTestFile = (filePath) => TEST_FILE_SUFFIXES.some((suffix) => filePath.endsWith(suffix));

const isAllowedPlacement = (relPath) => {
  const segments = relPath.split(path.sep);
  const base = path.basename(relPath);
  return segments.includes('__tests__') || base === 'route.test.ts' || base === 'route.test.tsx';
};

async function walk(dir) {
  const entries = await readdir(dir, { withFileTypes: true });
  const results = [];

  for (const entry of entries) {
    if (entry.name.startsWith('.git')) continue;
    if (entry.isDirectory()) {
      if (IGNORE_DIRS.has(entry.name)) continue;
      const childPath = path.join(dir, entry.name);
      results.push(...(await walk(childPath)));
    } else if (entry.isFile()) {
      const filePath = path.join(dir, entry.name);
      const relPath = path.relative(repoRoot, filePath);
      if (isTestFile(relPath)) {
        if (!isAllowedPlacement(relPath)) {
          results.push(relPath);
        }
      }
    }
  }

  return results;
}

async function main() {
  const violations = await walk(repoRoot);

  if (violations.length) {
    console.error('❌ Test placement violations found:');
    violations.forEach((v) => console.error(`  - ${v}`));
    process.exitCode = 1;
    return;
  }

  console.log('✅ Test placement looks good.');
}

main().catch((err) => {
  console.error(err);
  process.exitCode = 1;
});
