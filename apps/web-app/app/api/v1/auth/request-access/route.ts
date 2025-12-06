import { NextRequest, NextResponse } from 'next/server';

import { normalizeSignupGuardrailError } from '@/app/api/v1/auth/_utils/signupGuardrailResponses';
import { submitSignupAccessRequest } from '@/lib/server/services/auth/signupGuardrails';
import type { SignupAccessRequestInput } from '@/types/signup';

export async function POST(request: NextRequest) {
  try {
    const payload = (await request.json()) as SignupAccessRequestInput;
    const policy = await submitSignupAccessRequest(payload);
    return NextResponse.json(
      {
        success: true,
        policy,
      },
      { status: 202 },
    );
  } catch (error) {
    const normalized = normalizeSignupGuardrailError(error, 'Unable to submit access request.');
    return NextResponse.json(
      {
        success: false,
        error: normalized.message,
      },
      { status: normalized.status },
    );
  }
}
