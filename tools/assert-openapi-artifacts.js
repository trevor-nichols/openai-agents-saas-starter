/**
 * CI guard: ensure OpenAPI artifacts are consistent and deterministic.
 *
 * - apps/api-service/.artifacts/openapi.json is the canonical public spec.
 * - apps/api-service/.artifacts/openapi-fixtures.json may include test-only endpoints.
 */

import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const repoRoot = process.cwd();
const openapiPath = resolve(repoRoot, 'apps/api-service/.artifacts/openapi.json');
const fixturesPath = resolve(
  repoRoot,
  'apps/api-service/.artifacts/openapi-fixtures.json',
);

const requiredPaths = ['/api/v1/features'];

const fixtureOnlyPaths = [
  '/api/v1/test-fixtures/apply',
  '/api/v1/test-fixtures/email-verification-token',
  '/api/v1/test-fixtures/password-reset-token',
];

function loadJson(path) {
  try {
    return JSON.parse(readFileSync(path, 'utf-8'));
  } catch (error) {
    console.error(`❌ Failed to read OpenAPI artifact at ${path}:`, error);
    process.exit(1);
  }
}

function main() {
  const openapi = loadJson(openapiPath);
  const fixtures = loadJson(fixturesPath);

  const openapiPaths = new Set(Object.keys(openapi.paths ?? {}));
  const fixturesPaths = new Set(Object.keys(fixtures.paths ?? {}));

  const errors = [];

  for (const path of requiredPaths) {
    if (!openapiPaths.has(path)) {
      errors.push(`openapi.json missing required path: ${path}`);
    }
  }

  const onlyInFixtures = [...fixturesPaths].filter((p) => !openapiPaths.has(p));
  const onlyInOpenapi = [...openapiPaths].filter((p) => !fixturesPaths.has(p));

  if (onlyInOpenapi.length) {
    errors.push(
      `openapi.json contains paths missing from openapi-fixtures.json: ${onlyInOpenapi.join(
        ', ',
      )}`,
    );
  }

  const unexpectedFixtureOnly = onlyInFixtures.filter(
    (p) => !fixtureOnlyPaths.includes(p),
  );
  if (unexpectedFixtureOnly.length) {
    errors.push(
      `openapi-fixtures.json has unexpected extra paths: ${unexpectedFixtureOnly.join(
        ', ',
      )}`,
    );
  }

  const fixturePathsInOpenapi = fixtureOnlyPaths.filter((p) =>
    openapiPaths.has(p),
  );
  if (fixturePathsInOpenapi.length) {
    errors.push(
      `openapi.json must not include test fixtures: ${fixturePathsInOpenapi.join(
        ', ',
      )}`,
    );
  }

  if (errors.length) {
    console.error('❌ OpenAPI artifact validation failed:');
    for (const error of errors) {
      console.error(` - ${error}`);
    }
    process.exit(1);
  }

  console.log('✅ OpenAPI artifacts are consistent.');
}

main();
