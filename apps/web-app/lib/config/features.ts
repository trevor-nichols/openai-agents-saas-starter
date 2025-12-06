const TRUE_VALUES = new Set(['true', '1', 'yes']);

function parseBoolean(value?: string | null): boolean | null {
  if (value === undefined || value === null) return null;
  return TRUE_VALUES.has(value.toLowerCase()) ? true : false;
}

// Default posture: billing off unless explicitly enabled. Tests default to on for convenience.
const rawFlag =
  process.env.NEXT_PUBLIC_ENABLE_BILLING ??
  (process.env.NODE_ENV === 'test' ? 'true' : undefined);

export const billingEnabled = parseBoolean(rawFlag) ?? false;
