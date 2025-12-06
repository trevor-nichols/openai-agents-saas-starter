import type { SignupAccessPolicyMode } from '@/types/signup';

export interface AccessRequestSubmission {
  email: string;
  organization: string;
  policy: SignupAccessPolicyMode;
}
