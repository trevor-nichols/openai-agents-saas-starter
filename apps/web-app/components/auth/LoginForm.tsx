'use client';

import { useRouter } from 'next/navigation';
import { z } from 'zod';

import { loginAction } from '@/app/actions/auth';
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
import { useAuthForm } from '@/hooks/useAuthForm';

const loginSchema = z.object({
  email: z.string().trim().min(1, 'Email is required.').email('Enter a valid email address.'),
  password: z.string().min(8, 'Password must be at least 8 characters.'),
  tenantId: z
    .string()
    .trim()
    .optional()
    .or(z.literal('')),
});

type LoginFormValues = z.infer<typeof loginSchema>;
const defaultValues: LoginFormValues = {
  email: '',
  password: '',
  tenantId: '',
};

export function LoginForm({ redirectTo }: { redirectTo?: string }) {
  const router = useRouter();
  const safeRedirect = redirectTo && redirectTo.startsWith('/') ? redirectTo : '/dashboard';

  const { form, onSubmit, isSubmitting, formError } = useAuthForm<typeof loginSchema>({
    schema: loginSchema,
    initialValues: defaultValues,
    submitHandler: async (values) => {
      return loginAction({
        email: values.email,
        password: values.password,
        tenantId: values.tenantId?.trim() ? values.tenantId.trim() : undefined,
      });
    },
    successToast: {
      title: 'Signed in',
      description: 'Redirecting you to your workspace.',
    },
    errorToast: {
      title: 'Unable to sign in',
      description: 'Please double-check your credentials and try again.',
    },
    onSuccess: () => {
      router.push(safeRedirect);
      router.refresh();
    },
  });

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
                <Input
                  {...field}
                  type="email"
                  inputMode="email"
                  placeholder="you@example.com"
                  autoComplete="email"
                />
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
                <PasswordInput {...field} placeholder="••••••••" autoComplete="current-password" />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="tenantId"
          render={({ field }) => (
            <FormItem>
              <FormLabel>
                Tenant ID <span className="text-muted-foreground">(optional)</span>
              </FormLabel>
              <FormControl>
                <Input
                  {...field}
                  value={field.value ?? ''}
                  placeholder="UUID or slug (if required)"
                  autoComplete="organization"
                />
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
          {isSubmitting ? 'Signing in...' : 'Sign in'}
        </Button>
      </form>
    </Form>
  );
}
