'use client';

import { useState } from 'react';
import { z } from 'zod';

import { requestPasswordResetAction } from '@/app/actions/auth/passwords';
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
import { useToast } from '@/components/ui/use-toast';
import { useAuthForm } from '@/hooks/useAuthForm';

const forgotSchema = z.object({
  email: z.string().email('Enter a valid email address.'),
});

export function ForgotPasswordForm() {
  const [status, setStatus] = useState<'idle' | 'sent'>('idle');
  const [lastEmail, setLastEmail] = useState<string>('');
  const [isResending, setIsResending] = useState(false);
  const { info, error } = useToast();

  const { form, onSubmit, isSubmitting, formError } = useAuthForm<typeof forgotSchema>({
    schema: forgotSchema,
    initialValues: { email: '' },
    submitHandler: async (values) => {
      await requestPasswordResetAction({ email: values.email });
      setLastEmail(values.email);
    },
    successToast: {
      title: 'Reset link sent',
      description: 'Check your inbox for the secure reset link.',
    },
    errorToast: {
      title: 'Unable to send reset link',
      description: 'Please verify the email address and try again.',
    },
    onSuccess: () => setStatus('sent'),
  });

  const handleResend = async () => {
    if (!lastEmail) return;
    setIsResending(true);
    try {
      await requestPasswordResetAction({ email: lastEmail });
      info({
        title: 'Reset link resent',
        description: `We resent the link to ${lastEmail}.`,
      });
    } catch (err) {
      error({
        title: 'Unable to resend',
        description: err instanceof Error ? err.message : 'Try again shortly.',
      });
    } finally {
      setIsResending(false);
    }
  };

  if (status === 'sent') {
    return (
      <div className="space-y-4 text-sm">
        <p>
          We sent a password reset link to <span className="font-medium">{lastEmail}</span>. The link expires in 15
          minutes.
        </p>
        <Button type="button" variant="secondary" className="w-full" disabled={isResending} onClick={handleResend}>
          {isResending ? 'Sending again...' : 'Resend email'}
        </Button>
      </div>
    );
  }

  return (
    <Form {...form}>
      <form className="space-y-6" onSubmit={onSubmit} noValidate>
        <FormField
          control={form.control}
          name="email"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Email</FormLabel>
              <FormControl>
                <Input {...field} type="email" inputMode="email" autoComplete="email" placeholder="you@example.com" />
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

        <Button className="w-full" type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Sending link...' : 'Send reset link'}
        </Button>
      </form>
    </Form>
  );
}
