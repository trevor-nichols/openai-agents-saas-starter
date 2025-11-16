import { SignupGuardrailServiceError } from '@/lib/server/services/auth/signupGuardrails';

interface NormalizedError {
  status: number;
  message: string;
}

export function normalizeSignupGuardrailError(
  error: unknown,
  fallbackMessage: string,
): NormalizedError {
  if (error instanceof SignupGuardrailServiceError) {
    return { status: error.status, message: error.message };
  }

  if (error instanceof Error) {
    return {
      status: mapErrorToStatus(error.message),
      message: error.message || fallbackMessage,
    };
  }

  return { status: 500, message: fallbackMessage };
}

function mapErrorToStatus(message: string): number {
  const normalized = (message ?? '').toLowerCase();
  if (normalized.includes('missing access token')) {
    return 401;
  }
  if (normalized.includes('forbidden') || normalized.includes('permission')) {
    return 403;
  }
  if (normalized.includes('not found')) {
    return 404;
  }
  if (normalized.includes('rate limit')) {
    return 429;
  }
  if (normalized.includes('validation')) {
    return 422;
  }
  return 500;
}
