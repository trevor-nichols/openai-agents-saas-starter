import fs from 'node:fs/promises';

import { getFixturesPath } from './testEnv';

interface FixtureUserResult {
  user_id: string;
  role: string;
}

interface FixtureConversationResult {
  conversation_id: string;
  status: string;
}

export interface FixtureTenantResult {
  tenant_id: string;
  plan_code: string | null;
  users: Record<string, FixtureUserResult>;
  conversations: Record<string, FixtureConversationResult>;
}

export interface FixtureFile {
  tenants: Record<string, FixtureTenantResult>;
  generated_at: string;
}

let cachedFixtures: Promise<FixtureFile> | null = null;

async function readFixtureFile(): Promise<FixtureFile> {
  const fixturePath = getFixturesPath();
  try {
    const payload = await fs.readFile(fixturePath, 'utf8');
    const parsed = JSON.parse(payload) as FixtureFile;
    if (!parsed?.tenants) {
      throw new Error('Fixture file missing tenant data. Re-run `pnpm test:seed`.');
    }
    return parsed;
  } catch (error) {
    const hint =
      error instanceof Error
        ? `${error.message}. Did you run \`pnpm test:seed\` with USE_TEST_FIXTURES=true?`
        : 'Unable to read fixtures file.';
    throw new Error(hint);
  }
}

export async function getFixtures(): Promise<FixtureFile> {
  if (!cachedFixtures) {
    cachedFixtures = readFixtureFile();
  }
  return cachedFixtures;
}

export async function requireTenantFixture(slug: string): Promise<FixtureTenantResult> {
  const fixtures = await getFixtures();
  const tenant = fixtures.tenants[slug];
  if (!tenant) {
    throw new Error(`Tenant fixture '${slug}' not found. Update seeds/playwright.yaml and re-seed.`);
  }
  return tenant;
}

export async function getTenantId(slug: string): Promise<string> {
  const tenant = await requireTenantFixture(slug);
  if (!tenant.tenant_id) {
    throw new Error(`Tenant '${slug}' missing tenant_id in fixtures.`);
  }
  return tenant.tenant_id;
}

export async function getConversationId(tenantSlug: string, key: string): Promise<string> {
  const tenant = await requireTenantFixture(tenantSlug);
  const conversation = tenant.conversations[key];
  if (!conversation) {
    throw new Error(`Conversation '${key}' not found under tenant '${tenantSlug}'.`);
  }
  return conversation.conversation_id;
}

export async function getUserId(tenantSlug: string, email: string): Promise<string> {
  const tenant = await requireTenantFixture(tenantSlug);
  const normalized = email.toLowerCase();
  const entry = tenant.users[normalized];
  if (!entry) {
    throw new Error(`User '${email}' not found under tenant '${tenantSlug}'.`);
  }
  return entry.user_id;
}
