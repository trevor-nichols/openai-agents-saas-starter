'use client';

import { z } from 'zod';

import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
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
import { Textarea } from '@/components/ui/textarea';
import { useAuthForm } from '@/hooks/useAuthForm';
import { useSubmitSignupAccessRequestMutation } from '@/lib/queries/signup';
import { resolveSignupPolicyMode, type SignupAccessPolicyMode } from '@/types/signup';

const accessRequestSchema = z.object({
  fullName: z.string().min(2, 'Enter your full name.'),
  organization: z.string().min(2, 'Organization is required.'),
  email: z.string().email('Enter a valid email.'),
  message: z.string().max(500, 'Keep the summary under 500 characters.').optional(),
  acceptTerms: z
    .boolean()
    .refine((value) => value === true, { message: 'You must accept the Terms of Service.' }),
  honeypot: z.string().optional(),
});

const defaultValues = {
  fullName: '',
  organization: '',
  email: '',
  message: '',
  acceptTerms: false,
  honeypot: '',
};

interface AccessRequestFormProps {
  onSubmitted: (payload: { policy: SignupAccessPolicyMode; email: string; organization: string }) => void;
}

export function AccessRequestForm({ onSubmitted }: AccessRequestFormProps) {
  const mutation = useSubmitSignupAccessRequestMutation();

  const { form, onSubmit, isSubmitting, formError } = useAuthForm({
    schema: accessRequestSchema,
    initialValues: defaultValues,
    submitHandler: async (values) => {
      const policy = await mutation.mutateAsync({
        email: values.email,
        organization: values.organization,
        fullName: values.fullName,
        message: values.message?.trim() || undefined,
        acceptTerms: values.acceptTerms,
        honeypot: values.honeypot?.trim() || undefined,
      });
      onSubmitted({
        policy: resolveSignupPolicyMode(policy),
        email: values.email,
        organization: values.organization,
      });
    },
    successToast: {
      title: 'Request received',
      description: 'We will review your submission shortly.',
    },
    errorToast: {
      title: 'Submission failed',
      description: 'Please review the form and try again.',
    },
  });

  return (
    <Form {...form}>
      <form className="space-y-6" onSubmit={onSubmit} noValidate>
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
                <Input {...field} autoComplete="organization" placeholder="Anything Agents" />
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
              <FormLabel>Work email</FormLabel>
              <FormControl>
                <Input {...field} type="email" inputMode="email" autoComplete="email" placeholder="you@example.com" />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="message"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Use case</FormLabel>
              <FormDescription>Tell us how you plan to use the starter. Optional but helpful.</FormDescription>
              <FormControl>
                <Textarea {...field} rows={4} placeholder="Share the team, use case, and go-live timeline." />
              </FormControl>
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

        <FormField
          control={form.control}
          name="honeypot"
          render={({ field }) => (
            <FormItem className="sr-only" aria-hidden>
              <FormLabel>Leave empty</FormLabel>
              <FormControl>
                <Input {...field} tabIndex={-1} autoComplete="off" />
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
          {isSubmitting ? 'Submitting…' : 'Request access'}
        </Button>
      </form>
    </Form>
  );
}
