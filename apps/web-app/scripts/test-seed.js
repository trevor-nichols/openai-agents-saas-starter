#!/usr/bin/env node
/**
 * Deterministic seed runner for Playwright critical flow tests.
 *
 * Reads a YAML specification describing tenants, users, and billing fixtures,
 * invokes the backend test-fixtures endpoint, and writes the generated IDs to
 * `tests/.fixtures.json` for Playwright helpers.
 */

const fs = require('node:fs/promises');
const path = require('node:path');
const process = require('node:process');

const yaml = require('yaml');

const projectRoot = path.resolve(__dirname, '..');
const defaultSpecPath = path.join(projectRoot, 'seeds', 'playwright.yaml');
const defaultOutputPath = path.join(projectRoot, 'tests', '.fixtures.json');

function parseArgs(argv) {
  const args = argv.slice(2);
  const options = {
    specPath: process.env.PLAYWRIGHT_SEED_FILE || defaultSpecPath,
    outputPath: defaultOutputPath,
  };

  for (let index = 0; index < args.length; index += 1) {
    const arg = args[index];
    if (arg === '--spec' && args[index + 1]) {
      options.specPath = args[index + 1];
      index += 1;
    } else if (arg === '--output' && args[index + 1]) {
      options.outputPath = args[index + 1];
      index += 1;
    } else if (arg === '--help' || arg === '-h') {
      printUsage();
      process.exit(0);
    }
  }

  return options;
}

function printUsage() {
  console.log(
    [
      'Usage: pnpm test:seed [--spec path/to/spec.yaml] [--output path/to/output.json]',
      '',
      'Environment variables:',
      '  PLAYWRIGHT_API_URL      Override backend URL (default http://localhost:8000)',
      '  PLAYWRIGHT_SEED_FILE    Alternative spec file path',
    ].join('\n'),
  );
}

async function loadSpec(specPath) {
  const absolutePath = path.resolve(specPath);
  const payload = await fs.readFile(absolutePath, 'utf8');
  const parsed = yaml.parse(payload);
  if (!parsed || typeof parsed !== 'object' || !Array.isArray(parsed.tenants)) {
    throw new Error(
      `Seed specification ${absolutePath} must include a top-level "tenants" array.`,
    );
  }
  return parsed;
}

async function applyFixtures(apiUrl, spec) {
  const endpoint = new URL('/api/v1/test-fixtures/apply', apiUrl).toString();
  const response = await fetch(endpoint, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(spec),
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(
      `Backend rejected fixture payload (${response.status} ${response.statusText}): ${text}`,
    );
  }

  return response.json();
}

async function writeOutput(outputPath, payload) {
  const absolutePath = path.resolve(outputPath);
  await fs.mkdir(path.dirname(absolutePath), { recursive: true });
  await fs.writeFile(absolutePath, JSON.stringify(payload, null, 2));
  return absolutePath;
}

async function main() {
  const options = parseArgs(process.argv);
  const apiUrl =
    process.env.PLAYWRIGHT_API_URL ||
    process.env.NEXT_PUBLIC_API_URL ||
    'http://localhost:8000';

  try {
    const spec = await loadSpec(options.specPath);
    console.log(`Seeding fixtures via ${apiUrl}...`);

    const result = await applyFixtures(apiUrl, spec);
    const outputPath = await writeOutput(options.outputPath, result);

    console.log(`Fixture seeding complete. Results written to ${outputPath}`);
  } catch (error) {
    console.error(error instanceof Error ? error.message : error);
    process.exitCode = 1;
  }
}

void main();
