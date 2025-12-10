import type { MfaChallengeResponse } from '@/lib/api/client/types.gen';

export type LoginMode = 'success' | 'mfa';

let loginMode: LoginMode = 'success';

export const setLoginMode = (mode: LoginMode) => {
  loginMode = mode;
};

const demoChallenge: MfaChallengeResponse = {
  challenge_token: 'mfa_tok_story',
  methods: [
    { id: 'totp-1', method_type: 'totp', label: 'Authenticator App' },
    { id: 'sms-1', method_type: 'sms', label: 'SMS to ••••1234' },
  ],
};

export const loginAction = async () => {
  if (loginMode === 'mfa') return { mfa: demoChallenge };
  return { success: true };
};
