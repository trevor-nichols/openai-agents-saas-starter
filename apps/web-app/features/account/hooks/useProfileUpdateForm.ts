'use client';

import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';

import type { CurrentUserProfileResponseData } from '@/lib/api/client/types.gen';
import { useUpdateCurrentUserProfileMutation } from '@/lib/queries/users';
import { useToast } from '@/components/ui/use-toast';
import {
  buildProfilePatch,
  createProfileFormValues,
  type ProfileFormValues,
} from '../utils/profileForm';
import { PROFILE_FIELD_LIMITS } from '../constants';

const profileSchema = z.object({
  displayName: z
    .string()
    .max(PROFILE_FIELD_LIMITS.displayName, 'Display name is too long.'),
  givenName: z.string().max(PROFILE_FIELD_LIMITS.givenName, 'Given name is too long.'),
  familyName: z.string().max(PROFILE_FIELD_LIMITS.familyName, 'Family name is too long.'),
  avatarUrl: z.string().max(PROFILE_FIELD_LIMITS.avatarUrl, 'Avatar URL is too long.'),
  timezone: z.string().max(PROFILE_FIELD_LIMITS.timezone, 'Timezone is too long.'),
  locale: z.string().max(PROFILE_FIELD_LIMITS.locale, 'Locale is too long.'),
});

export function useProfileUpdateForm(profile: CurrentUserProfileResponseData | null) {
  const mutation = useUpdateCurrentUserProfileMutation();
  const toast = useToast();
  const form = useForm<ProfileFormValues>({
    resolver: zodResolver(profileSchema),
    defaultValues: createProfileFormValues(profile),
  });

  useEffect(() => {
    if (form.formState.isDirty) {
      return;
    }
    form.reset(createProfileFormValues(profile));
  }, [form, profile, form.formState.isDirty]);

  const handleSubmit = form.handleSubmit(async (values) => {
    form.clearErrors('root');
    const dirtyFields = form.formState.dirtyFields;
    const patch = buildProfilePatch(values, dirtyFields);
    if (Object.keys(patch).length === 0) {
      form.setError('root', { message: 'No changes to save yet.' });
      return;
    }

    try {
      const updated = await mutation.mutateAsync(patch);
      const nextValues = createProfileFormValues(updated ?? profile);
      form.reset(nextValues);
      toast.success({
        title: 'Profile updated',
        description: 'Your profile details are now up to date.',
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Please try again shortly.';
      form.setError('root', { message });
      toast.error({
        title: 'Unable to update profile',
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
