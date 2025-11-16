import { NextResponse } from 'next/server';

import { normalizeSignupGuardrailError } from '@/app/api/auth/_utils/signupGuardrailResponses';
import { approveSignupRequest } from '@/lib/server/services/auth/signupGuardrails';
import type { ApproveSignupRequestInput } from '@/types/signup';

interface RouteParams {
  params: {
    requestId?: string;
  };
}

export async function POST(request: Request, { params }: RouteParams) {
  const requestId = params?.requestId;
  if (!requestId) {
    return NextResponse.json(
      {
        success: false,
        error: 'Request id is required.',
      },
      { status: 400 },
    );
  }

  try {
    const payload = (await request.json()) as ApproveSignupRequestInput;
    const decision = await approveSignupRequest(requestId, payload);
    return NextResponse.json(
      {
        success: true,
        data: decision,
      },
      { status: 200 },
    );
  } catch (error) {
    const normalized = normalizeSignupGuardrailError(error, 'Unable to approve signup request.');
    return NextResponse.json(
      {
        success: false,
        error: normalized.message,
      },
      { status: normalized.status },
    );
  }
}
