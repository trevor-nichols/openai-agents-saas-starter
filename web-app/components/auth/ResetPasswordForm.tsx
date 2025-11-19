'use client';

import { useRouter } from 'next/navigation';
import { z } from 'zod';

import { confirmPasswordResetAction } from '@/app/actions/auth/passwords';
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
import { useAuthForm } from '@/hooks/useAuthForm';

const resetSchema = z
  .object({
    password: z.string().min(12, 'Passwords must be at least 12 characters.'),
    confirmPassword: z.string().min(12, 'Please confirm your new password.'),
  })
  .refine((data) => data.password === data.confirmPassword, {
    path: ['confirmPassword'],
    message: 'Passwords must match.',
  });

type ResetValues = z.infer<typeof resetSchema>;

const defaultValues: ResetValues = {
  password: '',
  confirmPassword: '',
};

interface ResetPasswordFormProps {
  token: string;
}

export function ResetPasswordForm({ token }: ResetPasswordFormProps) {
  const router = useRouter();

  const { form, onSubmit, isSubmitting, formError } = useAuthForm<typeof resetSchema>({
    schema: resetSchema,
    initialValues: defaultValues,
    submitHandler: async (values) => {
      await confirmPasswordResetAction(
        {
          token,
          new_password: values.password,
        },
        { redirectTo: '/login' },
      );
    },
    successToast: {
      title: 'Password updated',
      description: 'You can now sign in with your new password.',
    },
    errorToast: {
      title: 'Unable to reset password',
      description: 'The token may be invalid or expired.',
    },
    onSuccess: () => {
      router.push('/login');
      router.refresh();
    },
  });

  return (
    <Form {...form}>
      <form className="space-y-6" onSubmit={onSubmit} noValidate>
        <FormField
          control={form.control}
          name="password"
          render={({ field }) => (
            <FormItem>
              <FormLabel>New password</FormLabel>
              <FormControl>
                <Input {...field} type="password" autoComplete="new-password" placeholder="Minimum 12 characters" />
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
                <Input {...field} type="password" autoComplete="new-password" placeholder="Re-enter password" />
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

        <Button type="submit" className="w-full" disabled={isSubmitting}>
          {isSubmitting ? 'Updating password...' : 'Update password'}
        </Button>
      </form>
    </Form>
  );
}
