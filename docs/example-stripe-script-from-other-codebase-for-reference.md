```ts

/********************************************************************************
 *                                                                              *
 *                             Import Statements                                *
 *                                                                              *
 *  This section imports necessary modules for the script to function,          *
 *  including modules for executing shell commands, file system operations,     *
 *  handling asynchronous operations, reading user input, generating random     *
 *  values, and working with file paths and operating system information.       *
 *                                                                              *
 ********************************************************************************/
import { exec } from 'node:child_process';
import { promises as fs } from 'node:fs';
import { promisify } from 'node:util';
import readline from 'node:readline';
import crypto from 'node:crypto';
import path from 'node:path';
import { setupPlatformOwnerUser } from './platform-owner-setup';
import { logger } from '@agenai/logging';

const execAsync = promisify(exec);

/********************************************************************************
 *                                                                              *
 *                             Helper Functions                                 *
 *                                                                              *
 *  This section defines helper functions used throughout the script.           *
 *  These functions include asking the user a question and checking if the      *
 *  Stripe CLI is installed and authenticated.                                  *
 *                                                                              *
 ********************************************************************************/
function question(query: string): Promise<string> {
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
  });

  return new Promise((resolve) =>
    rl.question(query, (ans) => {
      rl.close();
      resolve(ans);
    })
  );
}

async function checkStripeCLI() {
  logger.info('Step 1: Checking if Stripe CLI is installed and authenticated...', undefined, 'setup');
  try {
    await execAsync('stripe --version');
    logger.info('Stripe CLI is installed.', undefined, 'setup');

    // Check if Stripe CLI is authenticated
    try {
      await execAsync('stripe config --list');
      logger.info('Stripe CLI is authenticated.', undefined, 'setup');
    } catch {
      logger.warn('Stripe CLI is not authenticated or the authentication has expired.', undefined, 'setup');
      logger.info('Please run: stripe login', undefined, 'setup');
      const answer = await question(
        'Have you completed the authentication? (y/n): '
      );
      if (answer.toLowerCase() !== 'y') {
        logger.info('Please authenticate with Stripe CLI and run this script again.', undefined, 'setup');
        process.exit(1);
      }

      // Verify authentication after user confirms login
      try {
        await execAsync('stripe config --list');
        logger.info('Stripe CLI authentication confirmed.', undefined, 'setup');
      } catch {
        logger.error('Failed to verify Stripe CLI authentication. Please try again.', undefined, undefined, 'setup');
        process.exit(1);
      }
    }
  } catch {
    logger.error('Stripe CLI is not installed. Please install it and try again.', undefined, undefined, 'setup');
    logger.info('To install Stripe CLI, follow these steps:', undefined, 'setup');
    logger.info('1. Visit: https://docs.stripe.com/stripe-cli', undefined, 'setup');
    logger.info('2. Download and install the Stripe CLI for your operating system', undefined, 'setup');
    logger.info('3. After installation, run: stripe login', undefined, 'setup');
    logger.info('After installation and authentication, please run this setup script again.', undefined, 'setup');
    process.exit(1);
  }
}

/********************************************************************************
 *                                                                              *
 *                             Postgres Setup                                   *
 *                                                                              *
 *  This section handles the setup of the Postgres database, allowing the user   *
 *  to choose between a local Docker instance or a remote database. It also     *
 *  includes the function to set up the local Postgres instance using Docker.   *
 *                                                                              *
 ********************************************************************************/
async function getPostgresURL(): Promise<string> {
  logger.info('Step 2: Setting up Postgres', undefined, 'setup:db');
  const dbChoice = await question(
    'Do you want to use a local Postgres instance with Docker (L) or a remote Postgres instance (R)? (L/R): '
  );

  if (dbChoice.toLowerCase() === 'l') {
    logger.info('Setting up local Postgres instance with Docker...', undefined, 'setup:db');
    await setupLocalPostgres();
    return 'postgres://postgres:postgres@localhost:54322/postgres';
  } else {
    logger.info('You can find Postgres databases at: https://vercel.com/marketplace?category=databases', undefined, 'setup:db');
    return await question('Enter your POSTGRES_URL: ');
  }
}

async function setupLocalPostgres() {
  logger.info('Checking if Docker is installed...', undefined, 'setup:db');
  try {
    await execAsync('docker --version');
    logger.info('Docker is installed.', undefined, 'setup:db');
  } catch {
    logger.error('Docker is not installed. Please install Docker and try again.', undefined, undefined, 'setup:db');
    logger.info('To install Docker, visit: https://docs.docker.com/get-docker/', undefined, 'setup:db');
    process.exit(1);
  }

  logger.info('Creating docker-compose.yml file...', undefined, 'setup:db');
  const dockerComposeContent = `
services:
  postgres:
    image: postgres:16.4-alpine
    container_name: next_saas_starter_postgres
    environment:
      POSTGRES_DB: postgres
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "54322:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
`;

  await fs.writeFile(
    path.join(process.cwd(), 'docker-compose.yml'),
    dockerComposeContent
  );
  logger.info('docker-compose.yml file created.', undefined, 'setup:db');

  logger.info('Starting Docker container with `docker compose up -d`...', undefined, 'setup:db');
  try {
    await execAsync('docker compose up -d');
    logger.info('Docker container started successfully.', undefined, 'setup:db');
  } catch {
    logger.error('Failed to start Docker container. Please check your Docker installation and try again.', undefined, undefined, 'setup:db');
    process.exit(1);
  }
}

/********************************************************************************
 *                                                                              *
 *                             Stripe Setup                                     *
 *                                                                              *
 *  This section handles the setup of Stripe, including getting the Stripe      *
 *  secret key and creating a Stripe webhook.                                   *
 *                                                                              *
 ********************************************************************************/
async function getStripeSecretKey(): Promise<string> {
  logger.info('Step 3: Getting Stripe Secret Key', undefined, 'setup:stripe');
  logger.info('You can find your Stripe Secret Key at: https://dashboard.stripe.com/test/apikeys', undefined, 'setup:stripe');
  return await question('Enter your Stripe Secret Key: ');
}

async function getStripeWebhookSecret(): Promise<string> {
  logger.info('Step 4: Getting Stripe Webhook Secret', undefined, 'setup:stripe');
  logger.info('You can find your Stripe Webhook Secret at: https://dashboard.stripe.com/webhooks', undefined, 'setup:stripe');
  return await question('Enter your Stripe Webhook Secret: ');
}

/********************************************************************************
 *                                                                              *
 *                             Environment Setup                                *
 *                                                                              *
 *  This section handles getting environment variables from the user and        *
 *  writing them to a .env file.                                                *
 *                                                                              *
 ********************************************************************************/
function generateAuthSecret(): string {
  logger.info('Step 5: Generating AUTH_SECRET...', undefined, 'setup:env');
  return crypto.randomBytes(32).toString('hex');
}

async function getAuthSecret(): Promise<string> {
  logger.info('Step 5: Getting AUTH_SECRET...', undefined, 'setup:env');
  const useExisting = await question('Do you want to use your own AUTH_SECRET? (y/n): ');
  
  if (useExisting.toLowerCase() === 'y') {
    return await question('Enter your AUTH_SECRET: ');
  } else {
    logger.info('Generating a new AUTH_SECRET...', undefined, 'setup:env');
    return crypto.randomBytes(32).toString('hex');
  }
}

async function writeEnvFile(envVars: Record<string, string>) {
  logger.info('Step 6: Writing environment variables to .env', undefined, 'setup:env');
  const envContent = Object.entries(envVars)
    .map(([key, value]) => `${key}=${value}`)
    .join('\n');

  await fs.writeFile(path.join(process.cwd(), '.env'), envContent);
  logger.info('.env file created with the necessary variables.', undefined, 'setup:env');
}

// ------------------------------------------------------------------------------------------------
//                          Setup Development Environment
// ------------------------------------------------------------------------------------------------
async function setupDevEnvironment() {
  logger.info('\n🔧 Setting up development environment...', undefined, 'setup:env');
  
  try {
    const localDbUrl = await getPostgresURL();
    
    // Create .env.local file for development
    const devEnvVars: Record<string, string> = {
      POSTGRES_URL: localDbUrl,
      USE_LOCAL_DB: 'true',
      NODE_ENV: 'development',
      BASE_URL: 'http://localhost:3000',
      AUTH_SECRET: generateAuthSecret(),
    };
    
    // Add all other required environment variables from .env
    const existingEnvContent = await fs.readFile('.env', 'utf-8').catch(() => '');
    if (existingEnvContent) {
      const envLines = existingEnvContent.split('\n');
      for (const line of envLines) {
        if (line && !line.startsWith('#')) {
          const parts = line.split('=');
          if (parts.length >= 2) {
            const key = parts[0].trim();
            const value = parts.slice(1).join('=').trim();
            if (key && value && !devEnvVars[key]) {
              devEnvVars[key] = value;
            }
          }
        }
      }
    }
    
    // Write .env.local with development configuration
    await fs.writeFile('.env.local', Object.entries(devEnvVars)
      .map(([key, value]) => `${key}=${value}`)
      .join('\n'));
    
    logger.info('✅ Development environment setup complete!', undefined, 'setup:env');
    logger.info('   .env.local has been created with local database configuration.', undefined, 'setup:env');
    
    return true;
  } catch (error) {
    logger.error('❌ Error setting up development environment:', error as Error, undefined, 'setup:env');
    return false;
  }
}

/********************************************************************************
 *                                                                              *
 *                             Main Function                                    *
 *                                                                              *
 *  This is the main function that orchestrates the entire setup process.       *
 *  It calls all the necessary functions to check the Stripe CLI, set up the    *
 *  database, get the Stripe secret key and webhook secret, generate the        *
 *  authentication secret, and write all the environment variables to the .env  *
 *  file.                                                                       *
 *                                                                              *
 ********************************************************************************/
async function main() {
  await checkStripeCLI();

  const POSTGRES_URL = await getPostgresURL();
  const STRIPE_SECRET_KEY = await getStripeSecretKey();
  const STRIPE_WEBHOOK_SECRET = await getStripeWebhookSecret();
  const BASE_URL = 'http://localhost:3000';
  const AUTH_SECRET = await getAuthSecret();

  await writeEnvFile({
    POSTGRES_URL,
    STRIPE_SECRET_KEY,
    STRIPE_WEBHOOK_SECRET,
    BASE_URL,
    AUTH_SECRET,
  });

  logger.info('🎉 Setup completed successfully!', undefined, 'setup');

  // Add option for development setup
  logger.info('\nDo you want to:', undefined, 'setup');
  logger.info('1. Set up production environment', undefined, 'setup');
  logger.info('2. Set up development environment', undefined, 'setup');
  
  const setupChoice = await question('Enter your choice (1/2): ');
  
  if (setupChoice === '2') {
    // Development setup
    await setupLocalPostgres();
    await setupDevEnvironment();
    
    // Ask about platform-owner setup for development
    const setupPlatformOwner = await question('Do you want to create the platform-owner user (Trevor Nichols)? (y/n): ');
    if (setupPlatformOwner.toLowerCase() === 'y') {
      const PlatformOwnerResult = await setupPlatformOwnerUser();
      if (!PlatformOwnerResult.success) {
        logger.error('❌ Failed to create platform-owner user:', PlatformOwnerResult.message, undefined, 'setup');
      }
    }
  } else {
    // Production setup
    logger.info('Production setup selected. Please run the droplet-setup.ts script on your production server.', undefined, 'setup');
    logger.info('The droplet setup will automatically create the platform-owner user.', undefined, 'setup');
  }
}

main().catch((err) => {
  logger.error('Setup script failed', err as Error, undefined, 'setup');
});
```
