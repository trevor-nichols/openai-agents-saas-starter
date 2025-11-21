import { NextRequest, NextResponse } from 'next/server';
import { z } from 'zod';

import { getSessionMetaFromCookies } from '@/lib/auth/cookies';
import { resendStatusIncident } from '@/lib/server/services/statusSubscriptions';

const REQUIRED_SCOPE = 'status:manage';

const payloadSchema = z
  .object({
    severity: z.enum(['all', 'major', 'maintenance']).optional(),
    tenantId: z.string().uuid().optional().nullable(),
    tenant_id: z.string().uuid().optional().nullable(),
  })
  .transform((value) => ({
    severity: value.severity,
    tenantId: value.tenantId ?? value.tenant_id ?? null,
  }));

function mapErrorToStatus(message: string): number {
  const normalized = message.toLowerCase();
  if (normalized.includes('missing access token')) return 401;
  if (normalized.includes('forbidden') || normalized.includes('status:manage')) return 403;
  if (normalized.includes('not found')) return 404;
  if (normalized.includes('rate limit')) return 429;
  if (normalized.includes('invalid') || normalized.includes('payload')) return 400;
  return 500;
}

export async function POST(
  request: NextRequest,
  { params }: { params: { incidentId: string } },
) {
  const session = await getSessionMetaFromCookies();
  if (!session) {
    return NextResponse.json({ success: false, error: 'Missing access token.' }, { status: 401 });
  }
  if (!session.scopes?.includes(REQUIRED_SCOPE)) {
    return NextResponse.json(
      { success: false, error: 'Forbidden: status:manage scope required.' },
      { status: 403 },
    );
  }

  const incidentId = params.incidentId;
  if (!incidentId) {
    return NextResponse.json(
      { success: false, error: 'Incident id is required.' },
      { status: 400 },
    );
  }

  let payload: { severity?: 'all' | 'major' | 'maintenance'; tenantId: string | null };
  try {
    const json = await request.json().catch(() => ({}));
    payload = payloadSchema.parse(json);
  } catch (error) {
    const issues = error instanceof z.ZodError ? error.flatten() : undefined;
    return NextResponse.json(
      { success: false, error: 'Invalid payload.', issues },
      { status: 422 },
    );
  }

  try {
    const response = await resendStatusIncident(incidentId, {
      severity: payload.severity,
      tenant_id: payload.tenantId,
    });

    return NextResponse.json(
      { success: true, dispatched: response.dispatched },
      { status: 202 },
    );
  } catch (error) {
    const message =
      error instanceof Error ? error.message : 'Unable to resend incident notifications.';
    return NextResponse.json(
      { success: false, error: message },
      { status: mapErrorToStatus(message) },
    );
  }
}
