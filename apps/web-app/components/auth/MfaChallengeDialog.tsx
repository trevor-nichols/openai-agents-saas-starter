"use client";

import { useEffect, useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { useCompleteMfaChallengeMutation } from "@/lib/queries/mfa";
import type { MfaChallengeCompleteRequest, MfaChallengeResponse } from "@/lib/api/client/types.gen";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";

const mfaSchema = z.object({
  methodId: z.string().min(1, "Select a method"),
  code: z.string().min(6, "Enter the 6-digit code").max(8, "Code is too long"),
});

type MfaFormValues = z.infer<typeof mfaSchema>;

interface Props {
  open: boolean;
  challenge: MfaChallengeResponse | null;
  onClose: () => void;
  onSuccess: () => void;
}

export function MfaChallengeDialog({ open, challenge, onClose, onSuccess }: Props) {
  const [formError, setFormError] = useState<string | null>(null);
  const defaultMethod = useMemo(() => challenge?.methods?.[0]?.id ?? "", [challenge]);

  const form = useForm<MfaFormValues>({
    resolver: zodResolver(mfaSchema),
    defaultValues: { methodId: defaultMethod, code: "" },
  });

  useEffect(() => {
    form.reset({ methodId: defaultMethod, code: "" });
    form.clearErrors();
  }, [defaultMethod, form]);

  useEffect(() => {
    if (open) {
      setTimeout(() => setFormError(null), 0);
    }
  }, [open, challenge]);

  const mutation = useCompleteMfaChallengeMutation();

  const onSubmit = form.handleSubmit(async (values) => {
    setFormError(null);
    if (!challenge) return;
    const payload: MfaChallengeCompleteRequest = {
      challenge_token: challenge.challenge_token,
      method_id: values.methodId,
      code: values.code,
    };
    try {
      await mutation.mutateAsync(payload);
      onSuccess();
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unable to verify code.";
      setFormError(message);
    }
  });

  const methods = challenge?.methods ?? [];

  return (
    <Dialog open={open} onOpenChange={(value) => (value ? undefined : onClose())}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Verify your sign-in</DialogTitle>
          <DialogDescription>Enter the code from your authenticator to continue.</DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <Form {...form}>
            <form className="space-y-4" onSubmit={onSubmit}>
              <FormField
                control={form.control}
                name="methodId"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Choose a method</FormLabel>
                    <FormControl>
                      <RadioGroup
                        value={field.value}
                        onValueChange={field.onChange}
                        className="grid gap-2"
                      >
                        {methods.map((method) => (
                          <label
                            key={method.id}
                            className="flex items-center justify-between rounded-lg border px-3 py-2 text-sm hover:border-primary"
                          >
                            <div className="flex items-center gap-2">
                              <RadioGroupItem value={method.id} />
                              <div className="flex flex-col">
                                <span className="font-medium">{method.label || method.method_type}</span>
                                <span className="text-xs text-muted-foreground">{method.method_type.toUpperCase()}</span>
                              </div>
                            </div>
                          </label>
                        ))}
                      </RadioGroup>
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="code"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>One-time code</FormLabel>
                    <FormControl>
                      <Input
                        {...field}
                        inputMode="numeric"
                        pattern="[0-9]*"
                        maxLength={8}
                        placeholder="123456"
                        autoFocus
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

              <div className="flex justify-end gap-2">
                <Button type="button" variant="ghost" onClick={onClose} disabled={mutation.isPending}>
                  Cancel
                </Button>
                <Button type="submit" disabled={mutation.isPending}>
                  {mutation.isPending ? "Verifying..." : "Verify"}
                </Button>
              </div>
            </form>
          </Form>
        </div>
      </DialogContent>
    </Dialog>
  );
}
