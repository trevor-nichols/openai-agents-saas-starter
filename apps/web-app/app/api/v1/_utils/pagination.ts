export type ParsedLimit =
  | { ok: true; value: number | undefined }
  | { ok: false; error: string };

/**
 * Parse an optional positive integer limit query param.
 *
 * - `null`/empty -> `undefined` (caller should omit limit).
 * - non-numeric / <=0 -> error.
 */
export function parseOptionalLimit(raw: string | null): ParsedLimit {
  if (!raw) {
    return { ok: true, value: undefined };
  }
  const value = Number.parseInt(raw, 10);
  if (!Number.isFinite(value) || Number.isNaN(value) || value <= 0) {
    return { ok: false, error: 'limit must be a positive integer' };
  }
  return { ok: true, value };
}

