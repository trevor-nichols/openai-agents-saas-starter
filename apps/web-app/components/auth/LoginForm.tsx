"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { z } from "zod";

import { loginAction } from "@/app/actions/auth";
import { MfaChallengeDialog } from "@/components/auth/MfaChallengeDialog";
import { SsoProviderSection } from "@/components/auth/SsoProviderSection";
import { Button } from "@/components/ui/button";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormDescription,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { PasswordInput } from "@/components/ui/password-input";
import { useToast } from "@/components/ui/use-toast";
import { useAuthForm } from "@/hooks/useAuthForm";
import { useDebouncedValue } from "@/hooks/useDebouncedValue";
import type { MfaChallengeResponse } from "@/lib/api/client/types.gen";
import { resolveSafeRedirect, resolveTenantSelection } from "@/lib/auth/sso";
import { useSsoProvidersQuery, useStartSsoMutation } from "@/lib/queries/sso";

const loginSchema = z
  .object({
    email: z.string().trim().min(1, "Email is required.").email("Enter a valid email address."),
    password: z.string().min(8, "Password must be at least 8 characters."),
    tenantId: z.string().trim().optional().or(z.literal("")),
    tenantSlug: z.string().trim().optional().or(z.literal("")),
  })
  .superRefine((values, ctx) => {
    const tenantId = values.tenantId?.trim();
    const tenantSlug = values.tenantSlug?.trim();
    if (tenantId && tenantSlug) {
      const message = "Provide either tenant ID or tenant slug, not both.";
      ctx.addIssue({ code: z.ZodIssueCode.custom, path: ["tenantId"], message });
      ctx.addIssue({ code: z.ZodIssueCode.custom, path: ["tenantSlug"], message });
    }
  });

type LoginFormValues = z.infer<typeof loginSchema>;
const defaultValues: LoginFormValues = {
  email: "",
  password: "",
  tenantId: "",
  tenantSlug: "",
};

export function LoginForm({ redirectTo }: { redirectTo?: string }) {
  const router = useRouter();
  const safeRedirect = resolveSafeRedirect(redirectTo) ?? "/dashboard";
  const [mfaChallenge, setMfaChallenge] = useState<MfaChallengeResponse | null>(null);
  const [ssoError, setSsoError] = useState<string | null>(null);
  const [activeProvider, setActiveProvider] = useState<string | null>(null);
  const { error: errorToast } = useToast();

  const { form, onSubmit, isSubmitting, formError, clearFormError } =
    useAuthForm<typeof loginSchema>({
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
        title: "Signed in",
        description: "Redirecting you to your workspace.",
      },
      errorToast: {
        title: "Unable to sign in",
        description: "Please double-check your credentials and try again.",
      },
      onSuccess: () => {
        router.push(safeRedirect);
        router.refresh();
      },
      onMfaRequired: (payload) => {
        clearFormError();
        setMfaChallenge(payload as MfaChallengeResponse);
      },
    });

  const tenantIdValue = form.watch("tenantId");
  const tenantSlugValue = form.watch("tenantSlug");
  const normalizedTenantId = tenantIdValue?.trim() ?? "";
  const normalizedTenantSlug = tenantSlugValue?.trim() ?? "";
  const { selector: tenantSelector, conflict: tenantConflict } = useMemo(
    () =>
      resolveTenantSelection({
        tenantId: normalizedTenantId,
        tenantSlug: normalizedTenantSlug,
      }),
    [normalizedTenantId, normalizedTenantSlug],
  );
  const debouncedTenantId = useDebouncedValue(normalizedTenantId, 350);
  const debouncedTenantSlug = useDebouncedValue(normalizedTenantSlug, 350);
  const { selector: debouncedTenantSelector, conflict: debouncedTenantConflict } = useMemo(
    () =>
      resolveTenantSelection({
        tenantId: debouncedTenantId,
        tenantSlug: debouncedTenantSlug,
      }),
    [debouncedTenantId, debouncedTenantSlug],
  );
  const isTenantDebouncing =
    debouncedTenantId !== normalizedTenantId || debouncedTenantSlug !== normalizedTenantSlug;
  const emailValue = form.watch("email");
  const loginHint = useMemo(() => {
    const trimmed = emailValue?.trim();
    if (!trimmed) return null;
    return loginSchema.shape.email.safeParse(trimmed).success ? trimmed : null;
  }, [emailValue]);

  const providersQuery = useSsoProvidersQuery(
    isTenantDebouncing || debouncedTenantConflict ? null : debouncedTenantSelector,
  );
  const startSso = useStartSsoMutation();
  const providersError =
    providersQuery.error instanceof Error ? providersQuery.error.message : null;
  const isProvidersLoading =
    providersQuery.isLoading ||
    (Boolean(normalizedTenantId || normalizedTenantSlug) && isTenantDebouncing);

  const handleSsoStart = async (providerKey: string) => {
    if (tenantConflict) {
      setSsoError("Provide either tenant ID or tenant slug, not both.");
      return;
    }
    if (!tenantSelector) {
      setSsoError("Enter a tenant slug or ID to continue with SSO.");
      return;
    }
    setSsoError(null);
    setActiveProvider(providerKey);
    try {
      const response = await startSso.mutateAsync({
        provider: providerKey,
        tenantSelector,
        loginHint,
        redirectTo: safeRedirect,
      });
      window.location.href = response.authorize_url;
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Unable to start SSO. Please try again.";
      setSsoError(message);
      setActiveProvider(null);
      errorToast({
        title: "SSO unavailable",
        description: message,
      });
    }
  };

  return (
    <>
      <Form {...form}>
        <div className="space-y-6">
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
                    Tenant ID <span className="text-muted-foreground">(UUID, optional)</span>
                  </FormLabel>
                  <FormControl>
                    <Input
                      {...field}
                      value={field.value ?? ""}
                      placeholder="11111111-2222-3333-4444-555555555555"
                      autoComplete="organization"
                      onChange={(event) => {
                        field.onChange(event);
                        if (ssoError) {
                          setSsoError(null);
                        }
                      }}
                    />
                  </FormControl>
                  <FormDescription>
                    Password login uses tenant ID. Provide either tenant ID or tenant slug, not both.
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="tenantSlug"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>
                    Tenant slug <span className="text-muted-foreground">(SSO only)</span>
                  </FormLabel>
                  <FormControl>
                    <Input
                      {...field}
                      value={field.value ?? ""}
                      placeholder="acme"
                      autoComplete="organization"
                      onChange={(event) => {
                        field.onChange(event);
                        if (ssoError) {
                          setSsoError(null);
                        }
                      }}
                    />
                  </FormControl>
                  <FormDescription>
                    Used to discover SSO providers. Leave blank if using tenant ID.
                  </FormDescription>
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
              {isSubmitting ? "Signing in..." : "Sign in"}
            </Button>
          </form>

          <SsoProviderSection
            hasTenantSelection={Boolean(tenantSelector)}
            providers={providersQuery.data ?? []}
            isLoading={isProvidersLoading}
            error={ssoError ?? providersError}
            activeProvider={activeProvider}
            onSelect={(provider) => void handleSsoStart(provider.provider_key)}
          />
        </div>
      </Form>

      <MfaChallengeDialog
        open={Boolean(mfaChallenge)}
        challenge={mfaChallenge}
        onClose={() => setMfaChallenge(null)}
        onSuccess={() => {
          setMfaChallenge(null);
          router.push(safeRedirect);
          router.refresh();
        }}
      />
    </>
  );
}
