const forceSecureCookies = process.env.AGENT_FORCE_SECURE_COOKIES === 'true';
const allowInsecureCookies = process.env.AGENT_ALLOW_INSECURE_COOKIES === 'true';

export const shouldUseSecureCookies =
  forceSecureCookies || (process.env.NODE_ENV === 'production' && !allowInsecureCookies);

export const SECURE_COOKIE_BASE = {
  httpOnly: true,
  sameSite: 'lax' as const,
  secure: shouldUseSecureCookies,
  path: '/',
};

export const META_COOKIE_BASE = {
  httpOnly: false,
  sameSite: 'lax' as const,
  secure: shouldUseSecureCookies,
  path: '/',
};
