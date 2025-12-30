import { randomUUID } from 'node:crypto';

import { getApiBaseUrl } from '../harness/env';

export interface SignupAccount {
  fullName: string;
  organization: string;
  email: string;
  password: string;
}

interface EmailTokenResponse {
  token: string;
  user_id: string;
  expires_at: string;
}

export function buildSignupAccount(): SignupAccount {
  const slugParts = randomUUID().split('-');
  const suffix = (slugParts[0] ?? randomUUID()).slice(0, 8);
  const fullName = `Playwright Owner ${suffix}`;
  const organization = `Playwright Sandbox ${suffix}`;
  const email = `signup+${suffix}@example.com`;
  const password = `Pw!${suffix.toUpperCase()}${Date.now()}`;
  return { fullName, organization, email: email.toLowerCase(), password };
}

export async function issueEmailVerificationToken(email: string): Promise<EmailTokenResponse> {
  const response = await fetch(`${getApiBaseUrl()}/api/v1/test-fixtures/email-verification-token`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email }),
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`Unable to mint verification token for ${email}: ${response.status} ${detail}`);
  }

  const payload = (await response.json()) as EmailTokenResponse;
  if (!payload?.token) {
    throw new Error('Backend returned an empty email verification token payload.');
  }
  return payload;
}
