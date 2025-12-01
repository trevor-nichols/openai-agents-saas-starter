import { NextResponse } from 'next/server';

import { normalizeSignupGuardrailError } from '@/app/api/v1/auth/_utils/signupGuardrailResponses';
import { getSignupAccessPolicy } from '@/lib/server/services/auth/signupGuardrails';

export async function GET() {
  try {
    const policy = await getSignupAccessPolicy();
    return NextResponse.json(
      {
        success: true,
        policy,
      },
      { status: 200 },
    );
  } catch (error) {
    const normalized = normalizeSignupGuardrailError(error, 'Unable to load signup policy.');
    return NextResponse.json(
      {
        success: false,
        error: normalized.message,
      },
      { status: normalized.status },
    );
  }
}
