/**
 * Thin helpers around the fixture-only backend endpoints.
 * Intended for Playwright seeds and local deterministic setup.
 * These should not be wired into production UI flows.
 */

type PlaywrightFixtureSpec = {
  tenants?: Array<Record<string, unknown>>;
};

type FixtureApplyResult = {
  tenants: Record<string, unknown>;
  generated_at: string;
};

type EmailVerificationTokenRequest = {
  email: string;
  ip_address?: string | null;
  user_agent?: string | null;
};

type EmailVerificationTokenResponse = {
  token: string;
  user_id: string;
  expires_at: string;
};

type ClientOptions = { baseUrl?: string };

/**
 * Apply a test fixture spec (Playwright/local dev).
 * Accepts the raw PlaywrightFixtureSpec and forwards it directly as the request body.
 */
export async function applyTestFixtures(
  spec: PlaywrightFixtureSpec,
  options?: ClientOptions,
): Promise<FixtureApplyResult> {
  const baseUrl = options?.baseUrl ? options.baseUrl.replace(/\/$/, '') : '';
  const response = await fetch(`${baseUrl}/api/v1/test-fixtures/apply`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(spec),
  });

  if (!response.ok) {
    throw new Error(`Fixture apply failed (${response.status})`);
  }

  const data = (await response.json()) as FixtureApplyResult | undefined;
  if (!data) {
    throw new Error('Fixture apply returned empty response.');
  }
  return data;
}

/**
 * Issue an email verification token via the fixture-only endpoint.
 */
export async function issueEmailVerificationToken(
  request: EmailVerificationTokenRequest,
  options?: ClientOptions,
): Promise<EmailVerificationTokenResponse> {
  const baseUrl = options?.baseUrl ? options.baseUrl.replace(/\/$/, '') : '';
  const response = await fetch(`${baseUrl}/api/v1/test-fixtures/email-verification-token`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error(`Email verification token request failed (${response.status})`);
  }

  const data = (await response.json()) as EmailVerificationTokenResponse | undefined;
  if (!data) {
    throw new Error('Email verification token response was empty.');
  }
  return data;
}
