#!/usr/bin/env node

import { createInterface } from 'node:readline/promises';
import { stdin as input, stdout as output } from 'node:process';
import { setTimeout as delay } from 'node:timers/promises';
import { promisify } from 'node:util';
import { exec as execCallback, spawn } from 'node:child_process';
import * as fs from 'node:fs/promises';
import path from 'node:path';

const execAsync = promisify(execCallback);

const STRIPE_GUIDED_AUTH_URL = 'https://dashboard.stripe.com/stripe-cli/auth';
const REQUIRED_ENV_KEYS = ['STRIPE_SECRET_KEY', 'STRIPE_WEBHOOK_SECRET', 'STRIPE_PRODUCT_PRICE_MAP'] as const;

const rl = createInterface({ input, output });

process.on('exit', () => {
  rl.close();
});

process.on('SIGINT', () => {
  logger.warn('Received interrupt signal. Exiting.');
  rl.close();
  process.exit(1);
});

type EnvKey = (typeof REQUIRED_ENV_KEYS)[number];

type EnvMap = Record<string, string>;

class Logger {
  private format(level: string, message: string, scope?: string) {
    const timestamp = new Date().toISOString();
    return `[${timestamp}] [${level}]${scope ? ` [${scope}]` : ''} ${message}`;
  }

  info(message: string, scope?: string) {
    console.log(this.format('INFO', message, scope));
  }

  warn(message: string, scope?: string) {
    console.warn(this.format('WARN', message, scope));
  }

  error(message: string, scope?: string) {
    console.error(this.format('ERROR', message, scope));
  }

  success(message: string, scope?: string) {
    console.log(this.format('SUCCESS', message, scope));
  }
}

const logger = new Logger();

class EnvFile {
  static async load(relativePath: string): Promise<EnvFile> {
    const absPath = path.resolve(relativePath);
    try {
      const data = await fs.readFile(absPath, 'utf8');
      return new EnvFile(absPath, EnvFile.parse(data));
    } catch (error: any) {
      if (error.code === 'ENOENT') {
        return new EnvFile(absPath, []);
      }
      throw error;
    }
  }

  private static parse(content: string): string[] {
    return content.replace(/\r\n/g, '\n').split('\n');
  }

  private static serialize(lines: string[]): string {
    const body = lines.join('\n');
    return body.endsWith('\n') ? body : `${body}\n`;
  }

  private map: Map<string, { line: number; value: string }> = new Map();
  private dirty = false;

  constructor(private readonly filePath: string, private lines: string[]) {
    this.reindex();
  }

  private reindex() {
    this.map.clear();
    this.lines.forEach((line, index) => {
      const match = line.match(/^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$/);
      if (!match) {
        return;
      }
      this.map.set(match[1], { line: index, value: match[2] });
    });
  }

  has(key: string): boolean {
    return this.map.has(key);
  }

  get(key: string): string | undefined {
    const entry = this.map.get(key);
    if (!entry) return undefined;
    return EnvFile.stripQuotes(entry.value.trim());
  }

  set(key: string, value: string) {
    const serialized = EnvFile.quoteValue(value);
    const existing = this.map.get(key);
    if (existing) {
      this.lines[existing.line] = `${key}=${serialized}`;
      this.map.set(key, { line: existing.line, value: serialized });
    } else {
      this.lines.push(`${key}=${serialized}`);
      this.map.set(key, { line: this.lines.length - 1, value: serialized });
    }
    this.dirty = true;
  }

  async save() {
    if (!this.dirty) return;
    await fs.writeFile(this.filePath, EnvFile.serialize(this.lines), 'utf8');
    this.dirty = false;
  }

  private static stripQuotes(raw: string): string {
    if (!raw) {
      return '';
    }
    if ((raw.startsWith('"') && raw.endsWith('"')) || (raw.startsWith('\'') && raw.endsWith('\''))) {
      return raw.slice(1, -1).replace(/\\n/g, '\n').replace(/\\"/g, '"');
    }
    const hashIndex = raw.indexOf(' #');
    if (hashIndex >= 0) {
      return raw.slice(0, hashIndex).trim();
    }
    return raw;
  }

  private static quoteValue(value: string): string {
    const safe = /^[A-Za-z0-9_:@./-]+$/;
    if (safe.test(value)) {
      return value;
    }
    return `"${value.replace(/\\/g, '\\\\').replace(/"/g, '\\"')}"`;
  }
}

async function main() {
  logger.info('Welcome to the Stripe setup assistant.');
  logger.info('This utility will verify prerequisites, help with Postgres, and capture Stripe credentials.');

  await ensureStripeCLI();
  await maybePreparePostgres();

  const envLocal = await EnvFile.load('.env.local');
  const envFallback = await EnvFile.load('.env');
  const envCompose = await EnvFile.load('.env.compose');

  const aggregated = mergeEnvMaps(envLocal, envFallback, envCompose);

  await collectStripeConfig(envLocal, aggregated);
  await envLocal.save();

  logger.success('Stripe configuration saved to .env.local');
}

async function ensureStripeCLI() {
  logger.info('Step 1: Checking Stripe CLI installation/authentication...', 'stripe');
  try {
    const version = await execAsync('stripe --version');
    logger.success(`Stripe CLI detected (${version.stdout.trim()}).`, 'stripe');
  } catch {
    logger.error('Stripe CLI not found. Install it from https://docs.stripe.com/stripe-cli and re-run this script.', 'stripe');
    process.exit(1);
  }

  try {
    await execAsync('stripe config --list');
    logger.success('Stripe CLI already authenticated.', 'stripe');
  } catch {
    logger.warn('Stripe CLI appears unauthenticated or expired.', 'stripe');
    const openGuide = await promptYesNo('Open the official Stripe CLI auth page in your browser?');
    if (openGuide) {
      await openUrl(STRIPE_GUIDED_AUTH_URL);
      await delay(500);
    }

    const runLogin = await promptYesNo('Run `stripe login --interactive` now?');
    if (runLogin) {
      await runInteractiveCommand('stripe', ['login', '--interactive']);
    } else {
      logger.info('You can authenticate later via `stripe login`. Continuing...');
    }

    try {
      await execAsync('stripe config --list');
      logger.success('Stripe CLI authentication verified.', 'stripe');
    } catch {
      logger.error('Stripe CLI is still not authenticated. Please run `stripe login` and retry.', 'stripe');
      process.exit(1);
    }
  }
}

async function maybePreparePostgres() {
  logger.info('Step 2: Optional Postgres helper.', 'postgres');
  const bringUpDocker = await promptYesNo('Start/refresh the local Postgres stack via `make dev-up`?');
  if (bringUpDocker) {
    try {
      await runInteractiveCommand('make', ['dev-up']);
      logger.success('Docker stack started.', 'postgres');
    } catch (error: any) {
      logger.warn(`Unable to run make dev-up (${error.message ?? error}). Continuing...`, 'postgres');
    }
  }

  const shouldCheckDb = await promptYesNo('Check DATABASE_URL connectivity via psql?');
  if (!shouldCheckDb) {
    return;
  }

  const databaseUrl = await resolveDatabaseUrl();
  if (!databaseUrl) {
    logger.warn('No DATABASE_URL found. Skipping connectivity test.', 'postgres');
    return;
  }

  await verifyDatabaseConnection(databaseUrl);
}

async function resolveDatabaseUrl(): Promise<string | undefined> {
  const searchOrder = ['.env.local', '.env', '.env.compose'];
  for (const file of searchOrder) {
    try {
      const envFile = await EnvFile.load(file);
      const value = envFile.get('DATABASE_URL');
      if (value) {
        logger.info(`Using DATABASE_URL from ${file}.`, 'postgres');
        return value;
      }
    } catch {
      // ignore missing file
    }
  }

  if (process.env.DATABASE_URL) {
    logger.info('Using DATABASE_URL from current shell environment.', 'postgres');
    return process.env.DATABASE_URL;
  }

  const manual = await promptInput('Enter a DATABASE_URL to test (leave blank to skip): ');
  return manual || undefined;
}

async function verifyDatabaseConnection(databaseUrl: string) {
  const normalized = normalizeDatabaseUrl(databaseUrl);
  try {
    await execAsync(`psql "${normalized}" -c "\\q"`, { env: process.env });
    logger.success('Successfully connected to Postgres using psql.', 'postgres');
  } catch (error: any) {
    logger.warn(`psql connectivity test failed (${error.message ?? error}). Ensure Postgres is reachable or skip this step.`, 'postgres');
  }
}

function normalizeDatabaseUrl(url: string): string {
  let mutated = url.trim();
  mutated = mutated.replace(/^postgresql\+asyncpg/, 'postgresql');
  mutated = mutated.replace(/^postgresql/, 'postgres');
  return mutated;
}

async function collectStripeConfig(envLocal: EnvFile, aggregated: EnvMap) {
  logger.info('Step 3: Capture Stripe credentials.', 'stripe');
  const secretKey = await promptForSecret('STRIPE_SECRET_KEY', 'Stripe secret key', envLocal, aggregated);
  logger.info(`Stripe secret key saved (${mask(secretKey)}).`, 'stripe');

  const webhookSecret = await promptForSecret('STRIPE_WEBHOOK_SECRET', 'Stripe webhook signing secret', envLocal, aggregated);
  logger.info(`Stripe webhook secret saved (${mask(webhookSecret)}).`, 'stripe');

  const existingMapRaw = aggregated['STRIPE_PRODUCT_PRICE_MAP'];
  const existingMap = parsePriceMap(existingMapRaw);
  const updatedMap = await promptForPriceMap(existingMap);
  envLocal.set('STRIPE_PRODUCT_PRICE_MAP', JSON.stringify(updatedMap));
  logger.info(`Captured price map: ${JSON.stringify(updatedMap)}`, 'stripe');

  envLocal.set('ENABLE_BILLING', 'true');
  logger.info('ENABLE_BILLING set to true.', 'stripe');
}

async function promptForSecret(key: EnvKey, label: string, target: EnvFile, aggregated: EnvMap): Promise<string> {
  const existing = aggregated[key];
  if (existing) {
    const overwrite = await promptYesNo(`${label} already set (${mask(existing)}). Overwrite?`, false);
    if (!overwrite) {
      target.set(key, existing);
      return existing;
    }
  }

  while (true) {
    const value = await promptInput(`${label}: `);
    if (value.trim()) {
      target.set(key, value.trim());
      return value.trim();
    }
    logger.warn('Value cannot be empty. Please try again.');
  }
}

function parsePriceMap(raw: string | undefined): Record<string, string> {
  if (!raw) return {};
  try {
    return JSON.parse(raw);
  } catch {
    const entries: Record<string, string> = {};
    raw.split(',').forEach((chunk) => {
      const [key, value] = chunk.split('=').map((part) => part.trim());
      if (key && value) {
        entries[key] = value;
      }
    });
    return entries;
  }
}

async function promptForPriceMap(existing: Record<string, string>): Promise<Record<string, string>> {
  logger.info('Stripe price IDs map billing plans to Stripe products.', 'stripe');
  const working: Record<string, string> = { ...existing };
  const defaultPlans = Object.keys(existing).length > 0 ? Object.keys(existing) : ['starter', 'pro'];

  for (const plan of defaultPlans) {
    const current = working[plan];
    const promptLabel = `Stripe price ID for plan "${plan}"${current ? ` (${current})` : ''}: `;
    const answer = await promptInput(promptLabel, current ?? undefined);
    if (answer.trim()) {
      working[plan] = answer.trim();
    }
  }

  while (await promptYesNo('Add another plan mapping?', false)) {
    const planCode = await promptInput('Plan code: ');
    if (!planCode.trim()) {
      logger.warn('Plan code cannot be empty.');
      continue;
    }
    const priceId = await promptInput('Stripe price ID: ');
    if (!priceId.trim()) {
      logger.warn('Price ID cannot be empty.');
      continue;
    }
    working[planCode.trim()] = priceId.trim();
  }

  if (Object.keys(working).length === 0) {
    logger.warn('No plan mappings provided. At least one mapping is required.');
    return await promptForPriceMap({ starter: '', pro: '' });
  }

  return working;
}

const AGGREGATE_KEYS = [...REQUIRED_ENV_KEYS, 'DATABASE_URL'] as const;
type AggregateKey = (typeof AGGREGATE_KEYS)[number];

function mergeEnvMaps(...files: EnvFile[]): EnvMap {
  const merged: EnvMap = {};
  files.forEach((file) => {
    AGGREGATE_KEYS.forEach((key: AggregateKey) => {
      const value = file.get(key);
      if (value && !merged[key]) {
        merged[key] = value;
      }
    });
  });
  return merged;
}

async function promptInput(question: string, fallback?: string): Promise<string> {
  const suffix = fallback ? ` (leave blank to keep ${mask(fallback)})` : '';
  const answer = await rl.question(`${question}${suffix}`);
  if (!answer.trim() && fallback) {
    return fallback;
  }
  return answer;
}

async function promptYesNo(question: string, defaultYes = true): Promise<boolean> {
  const hint = defaultYes ? 'Y/n' : 'y/N';
  const answer = await rl.question(`${question} (${hint}) `);
  if (!answer && defaultYes) return true;
  if (!answer && !defaultYes) return false;
  const normalized = answer.trim().toLowerCase();
  return normalized === 'y' || normalized === 'yes';
}

async function openUrl(url: string) {
  const platform = process.platform;
  let command: string;
  let args: string[] = [];

  if (platform === 'darwin') {
    command = 'open';
    args = [url];
  } else if (platform === 'win32') {
    command = 'cmd';
    args = ['/c', 'start', '""', url];
  } else {
    command = 'xdg-open';
    args = [url];
  }

  try {
    await runDetachedCommand(command, args);
    logger.info(`Opened ${url} in your browser.`);
  } catch {
    logger.warn(`Unable to automatically open ${url}. Please visit it manually.`);
  }
}

async function runDetachedCommand(command: string, args: string[]) {
  return new Promise<void>((resolve, reject) => {
    const child = spawn(command, args, { stdio: 'ignore' });
    child.on('error', reject);
    child.on('close', () => resolve());
  });
}

async function runInteractiveCommand(command: string, args: string[]) {
  return new Promise<void>((resolve, reject) => {
    const child = spawn(command, args, { stdio: 'inherit' });
    child.on('error', reject);
    child.on('close', (code) => {
      if (code === 0) {
        resolve();
      } else {
        reject(new Error(`${command} exited with code ${code}`));
      }
    });
  });
}

function mask(value: string | undefined): string {
  if (!value) return '(empty)';
  if (value.length <= 6) return '*'.repeat(value.length);
  return `${value.slice(0, 4)}…${value.slice(-4)}`;
}

main().catch((error) => {
  logger.error(`Setup failed: ${error instanceof Error ? error.message : String(error)}`);
  process.exit(1);
});
