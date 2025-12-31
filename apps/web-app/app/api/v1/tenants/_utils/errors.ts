export function mapTeamErrorStatus(message: string): number {
  const normalized = message.toLowerCase();
  if (normalized.includes('missing access token')) return 401;
  if (normalized.includes('forbidden') || normalized.includes('owner-only')) return 403;
  if (normalized.includes('not found')) return 404;
  if (normalized.includes('conflict') || normalized.includes('already')) return 409;
  if (normalized.includes('invalid') || normalized.includes('validation')) return 400;
  if (normalized.includes('delivery')) return 502;
  return 500;
}
