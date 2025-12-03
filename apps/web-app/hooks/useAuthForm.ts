'use client';

import { useState } from 'react';
import { zodResolver } from '@hookform/resolvers/zod';
import { useForm, type DefaultValues, type Resolver, type UseFormReturn } from 'react-hook-form';
import { z } from 'zod';

import { useToast } from '@/components/ui/use-toast';

type ToastContent = {
  title: string;
  description?: string;
};

type AuthSchema = z.ZodObject<Record<string, z.ZodTypeAny>>;

type SubmitResult = { success?: boolean; error?: string } | void;

interface UseAuthFormOptions<TSchema extends AuthSchema> {
  schema: TSchema;
  initialValues: z.infer<TSchema>;
  submitHandler: (values: z.infer<TSchema>) => Promise<SubmitResult>;
  successToast?: ToastContent;
  errorToast?: ToastContent;
  onSuccess?: () => void;
}

export function useAuthForm<TSchema extends AuthSchema>({
  schema,
  initialValues,
  submitHandler,
  successToast,
  errorToast,
  onSuccess,
}: UseAuthFormOptions<TSchema>) {
  type FormValues = z.infer<TSchema>;

  const form = useForm<FormValues>({
    resolver: zodResolver(schema) as Resolver<FormValues>,
    defaultValues: initialValues as DefaultValues<FormValues>,
  }) as UseFormReturn<FormValues>;
  const { success, error } = useToast();
  const [formError, setFormError] = useState<string | null>(null);

  const onSubmit = form.handleSubmit(async (values) => {
    setFormError(null);
    try {
      const result = await submitHandler(values);

      const resultError = extractResultError(result);
      if (resultError) {
        setFormError(resultError);
        error({
          title: errorToast?.title ?? 'Request failed',
          description: resultError,
        });
        return;
      }

      if (successToast) {
        success(successToast);
      }
      onSuccess?.();
    } catch (err) {
      const description = getErrorMessage(err, errorToast?.description);
      setFormError(description);
      error({
        title: errorToast?.title ?? 'Request failed',
        description,
      });
    }
  });

  return {
    form,
    onSubmit,
    isSubmitting: form.formState.isSubmitting,
    formError,
    clearFormError: () => setFormError(null),
  };
}

function getErrorMessage(error: unknown, fallback?: string) {
  if (error instanceof Error && error.message) {
    return error.message;
  }
  if (typeof error === 'string' && error.length > 0) {
    return error;
  }
  return fallback ?? 'Something went wrong. Please try again.';
}

function extractResultError(result: SubmitResult): string | null {
  if (!result || typeof result !== 'object') return null;
  if ('error' in result && typeof result.error === 'string') {
    return result.error;
  }
  if ('success' in result && result.success === false) {
    return 'Request failed.';
  }
  return null;
}
