'use client';

import { useRouter } from 'next/navigation';
import { z } from 'zod';

import { registerTenantAction } from '@/app/actions/auth/signup';
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
import { Checkbox } from '@/components/ui/checkbox';
import { useAuthForm } from '@/hooks/useAuthForm';

const registerSchema = z.object({
  fullName: z.string().min(2, 'Enter your full name.'),
  organization: z.string().min(2, 'Organization name is required.'),
  email: z.string().email('Enter a valid email address.'),
  password: z.string().min(12, 'Passwords must be at least 12 characters.'),
  acceptTerms: z
    .boolean()
    .refine((value) => value === true, { message: 'You must accept the Terms of Service.' }),
});

type RegisterFormValues = z.infer<typeof registerSchema>;

const defaultValues: RegisterFormValues = {
  fullName: '',
  organization: '',
  email: '',
  password: '',
  acceptTerms: false,
};

export function RegisterForm() {
  const router = useRouter();

  const { form, onSubmit, isSubmitting, formError } = useAuthForm<typeof registerSchema>({
    schema: registerSchema,
    initialValues: defaultValues,
    submitHandler: async (values) => {
      await registerTenantAction(
        {
          email: values.email,
          password: values.password,
          tenant_name: values.organization,
          display_name: values.fullName,
          accept_terms: values.acceptTerms,
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
              <FormLabel>Email</FormLabel>
              <FormControl>
                <Input {...field} type="email" inputMode="email" autoComplete="email" placeholder="you@example.com" />
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
                <Input {...field} type="password" autoComplete="new-password" placeholder="Minimum 12 characters" />
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

        {formError ? (
          <p className="text-sm font-medium text-destructive" role="alert">
            {formError}
          </p>
        ) : null}

        <Button className="w-full" type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Creating account...' : 'Create account'}
        </Button>
      </form>
    </Form>
  );
}
