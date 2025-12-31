'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { z } from 'zod';

import { acceptTeamInviteAction } from '@/app/actions/auth/team-invites';
import { Button } from '@/components/ui/button';
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { PasswordInput } from '@/components/ui/password-input';
import { PasswordPolicyList } from '@/components/ui/foundation';
import { useAuthForm } from '@/hooks/useAuthForm';
import { useAcceptTeamInviteExistingMutation } from '@/lib/queries/team';
import { useToast } from '@/components/ui/use-toast';
import { PASSWORD_POLICY_RULES } from '@/lib/auth/passwordPolicy';

const acceptInviteSchema = z
  .object({
    token: z.string().min(1, 'Invite token is required.'),
    displayName: z.string().max(128, 'Display name is too long.').optional(),
    password: z.string().min(14, 'Password must be at least 14 characters.'),
    confirmPassword: z.string().min(1, 'Confirm your password.'),
  })
  .refine((values) => values.password === values.confirmPassword, {
    path: ['confirmPassword'],
    message: 'Passwords must match.',
  });

type AcceptInviteFormValues = z.infer<typeof acceptInviteSchema>;

interface AcceptInviteFormProps {
  initialToken?: string;
  canAcceptExisting?: boolean;
}

export function AcceptInviteForm({ initialToken, canAcceptExisting = false }: AcceptInviteFormProps) {
  const router = useRouter();
  const toast = useToast();
  const acceptExisting = useAcceptTeamInviteExistingMutation();
  const loginHref = initialToken
    ? `/login?redirectTo=${encodeURIComponent(`/accept-invite?token=${encodeURIComponent(initialToken)}`)}`
    : '/login';

  const { form, onSubmit, isSubmitting, formError } = useAuthForm({
    schema: acceptInviteSchema,
    initialValues: {
      token: initialToken ?? '',
      displayName: '',
      password: '',
      confirmPassword: '',
    },
    submitHandler: async (values: AcceptInviteFormValues) => {
      await acceptTeamInviteAction(
        {
          token: values.token.trim(),
          password: values.password,
          displayName: values.displayName?.trim() ? values.displayName.trim() : null,
        },
        { redirectTo: '/dashboard' },
      );
    },
    successToast: {
      title: 'Invite accepted',
      description: 'Welcome! Redirecting you to your workspace.',
    },
    errorToast: {
      title: 'Invite acceptance failed',
      description: 'Please review your invite details and try again.',
    },
    onSuccess: () => {
      router.push('/dashboard');
      router.refresh();
    },
  });

  const handleAcceptExisting = async () => {
    const token = form.getValues('token').trim();
    if (!token) {
      toast.error({
        title: 'Invite token required',
        description: 'Paste your invite token before accepting as your current user.',
      });
      return;
    }

    try {
      await acceptExisting.mutateAsync({ token });
      toast.success({
        title: 'Invite accepted',
        description: 'Your account now has access to this tenant.',
      });
    } catch (error) {
      const description = error instanceof Error ? error.message : 'Unable to accept invite.';
      toast.error({ title: 'Invite acceptance failed', description });
    }
  };

  return (
    <div className="space-y-6">
      {canAcceptExisting ? (
        <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
          <div className="space-y-2">
            <p className="text-sm font-semibold text-foreground">Already signed in?</p>
            <p className="text-sm text-foreground/70">
              You can accept this invite with your current account. If you want to sign in as a new
              user, use the form below.
            </p>
          </div>
          <Button
            type="button"
            variant="outline"
            className="mt-4"
            onClick={handleAcceptExisting}
            disabled={acceptExisting.isPending}
          >
            {acceptExisting.isPending ? 'Accepting…' : 'Accept as current user'}
          </Button>
          <p className="mt-3 text-xs text-foreground/60">
            Tip: to switch tenants after accepting, sign out and log back in with the invited tenant ID.
          </p>
        </div>
      ) : null}

      <Form {...form}>
        <form className="space-y-6" onSubmit={onSubmit} noValidate>
          <FormField
            control={form.control}
            name="token"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Invite token</FormLabel>
                <FormControl>
                  <Input {...field} placeholder="agent-XXXX-XXXX" autoComplete="one-time-code" />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="displayName"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Display name (optional)</FormLabel>
                <FormControl>
                  <Input {...field} placeholder="Ada Lovelace" autoComplete="name" />
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
                <FormLabel>Create password</FormLabel>
                <FormControl>
                  <PasswordInput {...field} autoComplete="new-password" placeholder="Minimum 14 characters" />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="confirmPassword"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Confirm password</FormLabel>
                <FormControl>
                  <PasswordInput {...field} autoComplete="new-password" placeholder="Repeat your password" />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          {formError ? (
            <p className="text-sm font-medium text-destructive" role="alert">
              {formError}
            </p>
          ) : null}

          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <PasswordPolicyList items={PASSWORD_POLICY_RULES} />
            <Button type="submit" className="md:w-auto" disabled={isSubmitting}>
              {isSubmitting ? 'Accepting…' : 'Accept invite'}
            </Button>
          </div>
        </form>
      </Form>

      <p className="text-sm text-foreground/70">
        Already have an account?{' '}
        <Link href={loginHref} className="text-primary underline">
          Sign in instead
        </Link>
        .
      </p>
    </div>
  );
}
