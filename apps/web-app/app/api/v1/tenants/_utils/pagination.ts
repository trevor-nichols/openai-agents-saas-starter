const DEFAULT_LIMIT = 50;
const MAX_LIMIT = 200;

type ParsedNumber =
  | { ok: true; value: number }
  | { ok: false; error: string };

export function parseLimitParam(value: string | null): ParsedNumber {
  if (!value) {
    return { ok: true, value: DEFAULT_LIMIT };
  }
  const parsed = Number.parseInt(value, 10);
  if (Number.isNaN(parsed) || parsed <= 0) {
    return { ok: false, error: 'limit must be a positive integer.' };
  }
  return { ok: true, value: Math.min(parsed, MAX_LIMIT) };
}

export function parseOffsetParam(value: string | null): ParsedNumber {
  if (!value) {
    return { ok: true, value: 0 };
  }
  const parsed = Number.parseInt(value, 10);
  if (Number.isNaN(parsed) || parsed < 0) {
    return { ok: false, error: 'offset must be a non-negative integer.' };
  }
  return { ok: true, value: parsed };
}
