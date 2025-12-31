import { spawn } from 'node:child_process';
import fs from 'node:fs/promises';
import path from 'node:path';

import { getFixtures, getFixturesPath, resetFixturesCache } from './fixtures';

async function fileExists(filePath: string): Promise<boolean> {
  try {
    await fs.access(filePath);
    return true;
  } catch {
    return false;
  }
}

export async function runSeed(): Promise<void> {
  await new Promise<void>((resolve, reject) => {
    const child = spawn('pnpm', ['test:seed'], {
      cwd: path.resolve(__dirname, '..', '..'),
      stdio: 'inherit',
      env: process.env,
    });
    child.on('exit', (code) => {
      if (code === 0) {
        resolve();
      } else {
        reject(new Error(`pnpm test:seed failed with exit code ${code ?? 'unknown'}`));
      }
    });
    child.on('error', reject);
  });
}

export async function ensureFixtures(options: {
  shouldSeed: boolean;
  skipSeed: boolean;
  apiBaseUrl: string;
}): Promise<void> {
  if (options.skipSeed) {
    return;
  }

  if (options.shouldSeed) {
    await runSeed();
    resetFixturesCache();
    await getFixtures();
    return;
  }

  const fixturesPath = getFixturesPath();
  const hasFixtures = await fileExists(fixturesPath);
  if (!hasFixtures) {
    throw new Error(
      `Missing Playwright fixtures at ${fixturesPath}. Run pnpm test:seed (targets ${options.apiBaseUrl}) or set PLAYWRIGHT_SEED_ON_START=true.`,
    );
  }

  await getFixtures();
}
