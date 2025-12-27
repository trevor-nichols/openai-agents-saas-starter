'use client';

import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';

import { useDisableCurrentUserAccountMutation } from '@/lib/queries/users';
import { useToast } from '@/components/ui/use-toast';
import { performClientLogout } from '../utils/logout';

const disableSchema = z.object({
  currentPassword: z.string().min(1, 'Enter your current password.'),
});

export type DisableAccountFormValues = z.infer<typeof disableSchema>;

interface DisableAccountFormOptions {
  onSuccess?: () => void;
}

export function useDisableAccountForm(options: DisableAccountFormOptions = {}) {
  const mutation = useDisableCurrentUserAccountMutation();
  const toast = useToast();
  const form = useForm<DisableAccountFormValues>({
    resolver: zodResolver(disableSchema),
    defaultValues: {
      currentPassword: '',
    },
  });

  const handleSubmit = form.handleSubmit(async (values) => {
    form.clearErrors('root');
    try {
      await mutation.mutateAsync({ current_password: values.currentPassword });
      toast.success({
        title: 'Account disabled',
        description: 'Your sessions have been revoked and access is now disabled.',
      });
      form.reset({ currentPassword: '' });
      options.onSuccess?.();
      setTimeout(() => {
        void performClientLogout();
      }, 1200);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Please try again shortly.';
      form.setError('root', { message });
      toast.error({
        title: 'Unable to disable account',
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
