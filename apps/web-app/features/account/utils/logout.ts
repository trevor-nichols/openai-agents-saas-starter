import { apiV1Path } from '@/lib/apiPaths';

export async function performClientLogout(redirectTo = '/login') {
  try {
    await fetch(apiV1Path('/auth/logout'), { method: 'POST', cache: 'no-store' });
  } catch (error) {
    console.error('[account] Logout request failed', error);
  } finally {
    window.location.href = redirectTo;
  }
}
