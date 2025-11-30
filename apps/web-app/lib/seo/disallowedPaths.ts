export const DISALLOWED_PATHS = [
  '/api',
  '/api/*',
  '/login',
  '/register',
  '/password',
  '/account',
  '/agents',
  '/billing',
  '/dashboard',
  '/workflows',
  '/chat',
  '/ops',
  '/settings',
] as const;

const normalizePath = (path: string) => {
  if (!path.startsWith('/')) return `/${path}`;
  return path;
};

export const isPathDisallowed = (path: string): boolean => {
  const normalized = normalizePath(path);

  return DISALLOWED_PATHS.some((rule) => {
    if (rule.endsWith('/*')) {
      const prefix = rule.slice(0, -1); // keep trailing slash
      return normalized.startsWith(prefix);
    }

    return normalized === rule || normalized.startsWith(`${rule}/`);
  });
};
