'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useMemo } from 'react';
import { z } from 'zod';

import { registerTenantAction } from '@/app/actions/auth/signup';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { Checkbox } from '@/components/ui/checkbox';
import { useAuthForm } from '@/hooks/useAuthForm';
import type { SignupAccessPolicy } from '@/types/signup';
import { resolveSignupPolicyMode, type SignupAccessPolicyMode } from '@/types/signup';

const baseRegisterSchema = z.object({
  fullName: z.string().min(2, 'Enter your full name.'),
  organization: z.string().min(2, 'Organization name is required.'),
  email: z.string().email('Enter a valid email address.'),
  password: z.string().min(12, 'Passwords must be at least 12 characters.'),
  acceptTerms: z
    .boolean()
    .refine((value) => value === true, { message: 'You must accept the Terms of Service.' }),
  inviteToken: z
    .string()
    .max(128, 'Invite tokens cannot exceed 128 characters.')
    .optional()
    .or(z.literal('').transform(() => undefined)),
});

type RegisterFormValues = z.infer<typeof baseRegisterSchema>;

const defaultValues: RegisterFormValues = {
  fullName: '',
  organization: '',
  email: '',
  password: '',
  acceptTerms: false,
  inviteToken: undefined,
};

const POLICY_COPY: Record<SignupAccessPolicyMode, { title: string; description: string; ctaLabel: string }> = {
  public: {
    title: 'Open signup',
    description: 'Provision a tenant instantly. Operators can disable public signup at any time.',
    ctaLabel: 'Learn more',
  },
  invite_only: {
    title: 'Invite required',
    description: 'Enter the invite token from your operator or request one to continue.',
    ctaLabel: 'Request access',
  },
  approval: {
    title: 'Approval required',
    description: 'Submit an access request to the team. Approved customers receive an invite token via email.',
    ctaLabel: 'Request access',
  },
};

interface RegisterFormProps {
  policy?: SignupAccessPolicy | null;
  requestAccessHref?: string;
}

export function RegisterForm({ policy, requestAccessHref = '/request-access' }: RegisterFormProps) {
  const router = useRouter();
  const policyMode = resolveSignupPolicyMode(policy);
  const requiresInviteToken = policyMode !== 'public';

  const schema = useMemo(
    () =>
      baseRegisterSchema.superRefine((values, ctx) => {
        if (!requiresInviteToken) {
          return;
        }
        const token = values.inviteToken?.trim();
        if (!token) {
          ctx.addIssue({
            code: z.ZodIssueCode.custom,
            message: 'Invite token is required.',
            path: ['inviteToken'],
          });
        }
      }),
    [requiresInviteToken],
  );

  const { form, onSubmit, isSubmitting, formError } = useAuthForm({
    schema,
    initialValues: defaultValues,
    submitHandler: async (values: RegisterFormValues) => {
      await registerTenantAction(
        {
          email: values.email,
          password: values.password,
          tenant_name: values.organization,
          display_name: values.fullName,
          accept_terms: values.acceptTerms,
          invite_token: values.inviteToken?.trim() || undefined,
        },
        { redirectTo: '/dashboard' },
      );
    },
    successToast: {
      title: 'Account created',
      description: 'Welcome aboard! Redirecting you to the dashboard.',
    },
    errorToast: {
      title: 'Registration failed',
      description: 'Please review the form and try again.',
    },
    onSuccess: () => {
      router.push('/dashboard');
      router.refresh();
    },
  });

  const policyCopy = POLICY_COPY[policyMode];

  return (
    <Form {...form}>
      <form className="space-y-6" onSubmit={onSubmit} noValidate>
        {policyMode !== 'public' ? (
          <Alert variant="default" className="border-primary/40 bg-primary/5 text-primary">
            <AlertTitle>{policyCopy.title}</AlertTitle>
            <AlertDescription>{policyCopy.description}</AlertDescription>
          </Alert>
        ) : null}

        <FormField
          control={form.control}
          name="fullName"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Full name</FormLabel>
              <FormControl>
                <Input {...field} autoComplete="name" placeholder="Ada Lovelace" />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="organization"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Organization</FormLabel>
              <FormControl>
                <Input {...field} autoComplete="organization" placeholder="Acme" />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="email"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Email</FormLabel>
              <FormControl>
                <Input
                  {...field}
                  type="email"
                  inputMode="email"
                  autoComplete="email"
                  placeholder="you@example.com"
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="password"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Password</FormLabel>
              <FormControl>
                <Input
                  {...field}
                  type="password"
                  autoComplete="new-password"
                  placeholder="Minimum 12 characters"
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="inviteToken"
          render={({ field }) => (
            <FormItem>
              <FormLabel className="flex items-center justify-between">
                Invite token
                {requiresInviteToken ? (
                  <span className="text-xs font-normal text-muted-foreground">Required</span>
                ) : (
                  <span className="text-xs font-normal text-muted-foreground">Optional</span>
                )}
              </FormLabel>
              <FormControl>
                <Input
                  {...field}
                  value={field.value ?? ''}
                  autoComplete="one-time-code"
                  placeholder="agent-XXXX-XXXX"
                />
              </FormControl>
              <FormDescription>
                Use the invite code from your approval email. Need one?{' '}
                <Link href={requestAccessHref} className="text-primary underline">
                  Request access
                </Link>
                .
              </FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="acceptTerms"
          render={({ field }) => (
            <FormItem className="space-y-3">
              <div className="flex items-start gap-3 rounded-lg border border-white/10 bg-white/5 p-4">
                <FormControl>
                  <Checkbox checked={field.value} onCheckedChange={(checked) => field.onChange(checked === true)} />
                </FormControl>
                <div className="space-y-1 text-sm">
                  <FormLabel className="font-normal">
                    I agree to the{' '}
                    <a href="/terms" className="text-primary underline">
                      Terms of Service
                    </a>{' '}
                    and acknowledge the{' '}
                    <a href="/privacy" className="text-primary underline">
                      Privacy Policy
                    </a>
                    .
                  </FormLabel>
                </div>
              </div>
              <FormMessage />
            </FormItem>
          )}
        />

        {formError ? (
          <p className="text-sm font-medium text-destructive" role="alert">
            {formError}
          </p>
        ) : null}

        <Button className="w-full" type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Creating account...' : 'Create account'}
        </Button>

        {policyMode !== 'public' ? (
          <Button asChild variant="outline" className="w-full">
            <Link href={requestAccessHref}>{policyCopy.ctaLabel}</Link>
          </Button>
        ) : null}
      </form>
    </Form>
  );
}
