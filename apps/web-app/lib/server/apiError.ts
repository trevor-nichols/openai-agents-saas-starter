import 'server-only';
/** Normalize errors thrown by the HeyAPI client (which throws parsed JSON objects when throwOnError=true)
 * into a { status, body } tuple suitable for NextResponse.json.
 */
export function normalizeApiError(error: unknown): { status: number; body: { message: string; detail?: string; error?: unknown } } {
  const fallback = { status: 500, body: { message: 'Internal server error' } } as const;

  const matchesUnauthorized = (msg: string | undefined) => {
    if (!msg) return false;
    const normalized = msg.toLowerCase();
    return normalized.includes('missing access token') || normalized.includes('unauthorized') || normalized.includes('invalid token');
  };

  // Handle objects (plain JSON payloads from the SDK)
  if (error && typeof error === 'object') {
    const errObj = error as Record<string, unknown>;
    const statusCandidates = ['status', 'status_code', 'code'];
    const status = statusCandidates
      .map((k) => errObj[k])
      .find((v) => typeof v === 'number') as number | undefined;

    const detail = typeof errObj.detail === 'string' ? errObj.detail : undefined;
    const message = typeof errObj.message === 'string' ? errObj.message : detail ?? 'Request failed';

    if (matchesUnauthorized(message) || matchesUnauthorized(detail)) {
      return {
        status: 401,
        body: { message, detail, error },
      };
    }

    return {
      status: status && status >= 100 && status < 600 ? status : (detail && detail.toLowerCase().includes('not found') ? 404 : fallback.status),
      body: {
        message,
        detail,
        error,
      },
    };
  }

  // Handle Error instances
  if (error instanceof Error) {
    const status = matchesUnauthorized(error.message) ? 401 : 500;
    return { status, body: { message: error.message, detail: error.message, error } };
  }

  return fallback;
}
