'use client';

import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';

import { useChangePasswordMutation } from '@/lib/queries/accountSecurity';
import { useToast } from '@/components/ui/use-toast';

const passwordSchema = z
  .object({
    currentPassword: z.string().min(1, 'Enter your current password.'),
    newPassword: z.string().min(14, 'New password must be at least 14 characters.'),
    confirmNewPassword: z.string().min(1, 'Confirm your new password.'),
  })
  .refine((values) => values.newPassword === values.confirmNewPassword, {
    path: ['confirmNewPassword'],
    message: 'Passwords must match.',
  });

export type PasswordFormValues = z.infer<typeof passwordSchema>;

export function usePasswordChangeForm() {
  const changePassword = useChangePasswordMutation();
  const toast = useToast();

  const form = useForm<PasswordFormValues>({
    resolver: zodResolver(passwordSchema),
    defaultValues: {
      currentPassword: '',
      newPassword: '',
      confirmNewPassword: '',
    },
  });

  const handleSubmit = form.handleSubmit(async (values) => {
    form.clearErrors('root');
    try {
      await changePassword.mutateAsync({
        current_password: values.currentPassword,
        new_password: values.newPassword,
      });
      toast.success({
        title: 'Password updated',
        description: 'All other sessions were signed out.',
      });
      form.reset();
    } catch (error) {
      const message =
        error instanceof Error ? error.message : 'Double-check your credentials and try again.';
      form.setError('root', { message });
      toast.error({ title: 'Unable to change password', description: message });
    }
  });

  return {
    form,
    onSubmit: handleSubmit,
    isSaving: changePassword.isPending,
    rootError: form.formState.errors.root?.message ?? null,
  };
}
