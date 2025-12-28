/**
 * CI guard: ensure billing endpoints remain in the committed OpenAPI artifact.
 *
 * Fails if any expected billing paths are missing from
 * apps/api-service/.artifacts/openapi.json.
 */

import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const artifactPath = resolve(process.cwd(), 'apps/api-service/.artifacts/openapi.json');
const requiredPaths = [
  '/api/v1/billing/plans',
  '/api/v1/billing/stream',
  '/api/v1/billing/tenants/{tenant_id}/events',
  '/api/v1/billing/tenants/{tenant_id}/payment-methods',
  '/api/v1/billing/tenants/{tenant_id}/payment-methods/setup-intent',
  '/api/v1/billing/tenants/{tenant_id}/payment-methods/{payment_method_id}',
  '/api/v1/billing/tenants/{tenant_id}/payment-methods/{payment_method_id}/default',
  '/api/v1/billing/tenants/{tenant_id}/portal',
  '/api/v1/billing/tenants/{tenant_id}/subscription',
  '/api/v1/billing/tenants/{tenant_id}/subscription/plan',
  '/api/v1/billing/tenants/{tenant_id}/subscription/cancel',
  '/api/v1/billing/tenants/{tenant_id}/upcoming-invoice',
  '/api/v1/billing/tenants/{tenant_id}/usage',
];

function main() {
  let spec;
  try {
    const raw = readFileSync(artifactPath, 'utf-8');
    spec = JSON.parse(raw);
  } catch (error) {
    console.error(`❌ Failed to read OpenAPI artifact at ${artifactPath}:`, error);
    process.exit(1);
  }

  const paths = spec && spec.paths ? Object.keys(spec.paths) : [];
  const missing = requiredPaths.filter((p) => !paths.includes(p));

  if (missing.length) {
    console.error('❌ Billing OpenAPI artifact is missing required paths:');
    for (const path of missing) {
      console.error(` - ${path}`);
    }
    console.error('Regenerate the SDK against the billing-enabled spec before merging.');
    process.exit(1);
  }

  console.log('✅ Billing OpenAPI artifact contains all required billing paths.');
}

main();
