export function formatRelativeTime(value: string | null | undefined): string {
  if (!value) return 'Unknown';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return 'Unknown';
  const diffMs = Date.now() - date.getTime();
  const minute = 60 * 1000;
  const hour = 60 * minute;
  const day = 24 * hour;

  if (diffMs < minute) return 'Just now';
  if (diffMs < hour) return `${Math.round(diffMs / minute)}m ago`;
  if (diffMs < day) return `${Math.round(diffMs / hour)}h ago`;
  return `${Math.round(diffMs / day)}d ago`;
}

export function formatClockTime(value: string | undefined): string {
  if (!value) return '';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '';
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

/**
 * Parse an ISO-ish timestamp to epoch ms.
 *
 * The backend sometimes emits timestamps with microseconds and/or without an explicit
 * timezone (e.g. `2025-12-14T03:46:39.123456`). Browsers can treat those as invalid,
 * which breaks ordering/anchoring logic in the chat UI.
 */
export function parseTimestampMs(value: string | null | undefined): number | null {
  if (!value) return null;
  let normalized = value.trim();
  if (!normalized) return null;

  // Truncate fractional seconds beyond milliseconds (JS Date parsing is inconsistent for microseconds).
  const fractionalMatch = normalized.match(/\.(\d+)(?=Z|[+-]\d{2}:?\d{2}$|$)/);
  if (fractionalMatch && fractionalMatch[1] && fractionalMatch[1].length > 3) {
    const truncated = fractionalMatch[1].slice(0, 3);
    normalized = normalized.replace(`.${fractionalMatch[1]}`, `.${truncated}`);
  }

  // If no timezone is present, assume UTC for stable cross-client ordering.
  const hasTimezone = /Z|[+-]\d{2}:?\d{2}$/.test(normalized);
  if (!hasTimezone) {
    normalized = `${normalized}Z`;
  }

  const ms = Date.parse(normalized);
  return Number.isFinite(ms) ? ms : null;
}
