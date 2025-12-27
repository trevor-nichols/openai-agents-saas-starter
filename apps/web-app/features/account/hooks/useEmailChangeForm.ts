'use client';

import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';

import type { CurrentUserProfileResponseData } from '@/lib/api/client/types.gen';
import { useChangeCurrentUserEmailMutation } from '@/lib/queries/users';
import { useToast } from '@/components/ui/use-toast';
import { performClientLogout } from '../utils/logout';

const emailSchema = z.object({
  newEmail: z.string().email('Enter a valid email.'),
  currentPassword: z.string().min(1, 'Enter your current password.'),
});

export type EmailChangeFormValues = z.infer<typeof emailSchema>;

export function useEmailChangeForm(profile: CurrentUserProfileResponseData | null) {
  const mutation = useChangeCurrentUserEmailMutation();
  const toast = useToast();
  const form = useForm<EmailChangeFormValues>({
    resolver: zodResolver(emailSchema),
    defaultValues: {
      newEmail: profile?.email ?? '',
      currentPassword: '',
    },
  });

  useEffect(() => {
    if (form.formState.isDirty) {
      return;
    }
    form.reset({
      newEmail: profile?.email ?? '',
      currentPassword: '',
    });
  }, [form, profile?.email, form.formState.isDirty]);

  const handleSubmit = form.handleSubmit(async (values) => {
    form.clearErrors('root');
    const trimmedEmail = values.newEmail.trim();
    const normalizedNew = trimmedEmail.toLowerCase();
    const normalizedCurrent = (profile?.email ?? '').trim().toLowerCase();

    if (!trimmedEmail) {
      form.setError('newEmail', { message: 'Enter a valid email.' });
      return;
    }

    if (normalizedNew === normalizedCurrent) {
      toast.success({
        title: 'Email already up to date',
        description: 'Enter a different address to make a change.',
      });
      form.reset({ newEmail: profile?.email ?? trimmedEmail, currentPassword: '' });
      return;
    }

    try {
      const result = await mutation.mutateAsync({
        current_password: values.currentPassword,
        new_email: trimmedEmail,
      });

      toast.success({
        title: 'Email updated',
        description: result.verification_sent
          ? 'We sent a verification email. Please confirm to continue.'
          : 'Your email is updated. Verification may still be required.',
      });

      form.reset({ newEmail: result.email ?? trimmedEmail, currentPassword: '' });

      setTimeout(() => {
        void performClientLogout();
      }, 1200);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Please try again shortly.';
      form.setError('root', { message });
      toast.error({
        title: 'Unable to update email',
        description: message,
      });
    }
  });

  return {
    form,
    onSubmit: handleSubmit,
    isSaving: mutation.isPending,
    rootError: form.formState.errors.root?.message ?? null,
  };
}
