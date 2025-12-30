import fs from 'node:fs/promises';
import path from 'node:path';

import { z } from 'zod';

const FixtureUserSchema = z.object({
  user_id: z.string().min(1),
  role: z.string().min(1),
});

const FixtureConversationSchema = z.object({
  conversation_id: z.string().min(1),
  status: z.string().min(1),
});

const FixtureAssetSchema = z.object({
  asset_id: z.string().min(1),
  storage_object_id: z.string().min(1),
});

const FixtureTenantSchema = z.object({
  tenant_id: z.string().min(1),
  plan_code: z.string().nullable(),
  users: z.record(z.string(), FixtureUserSchema),
  conversations: z.record(z.string(), FixtureConversationSchema),
  assets: z.record(z.string(), FixtureAssetSchema).default({}),
});

const FixtureFileSchema = z.object({
  tenants: z.record(z.string(), FixtureTenantSchema),
  generated_at: z.string().min(1),
});

export type FixtureFile = z.infer<typeof FixtureFileSchema>;
export type FixtureTenantResult = z.infer<typeof FixtureTenantSchema>;

let cachedFixtures: Promise<FixtureFile> | null = null;

export function getFixturesPath(): string {
  return path.resolve(__dirname, '..', '.fixtures.json');
}

async function readFixtureFile(): Promise<FixtureFile> {
  const fixturePath = getFixturesPath();
  try {
    const payload = await fs.readFile(fixturePath, 'utf8');
    const parsed = JSON.parse(payload) as unknown;
    const validated = FixtureFileSchema.parse(parsed);
    return validated;
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unable to read fixtures file.';
    throw new Error(`${message}. Did you run \`pnpm test:seed\` with USE_TEST_FIXTURES=true?`);
  }
}

export async function getFixtures(): Promise<FixtureFile> {
  if (!cachedFixtures) {
    cachedFixtures = readFixtureFile();
  }
  return cachedFixtures;
}

export function resetFixturesCache(): void {
  cachedFixtures = null;
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
