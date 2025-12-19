"use client";

import { useMemo, useState } from "react";
import { AlertCircle, ShieldCheck, ShieldOff } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { GlassPanel, SectionHeader } from "@/components/ui/foundation";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { useToast } from "@/components/ui/use-toast";
import {
  useMfaMethodsQuery,
  useRevokeMfaMethodMutation,
  useRegenerateRecoveryCodesMutation,
  useStartTotpEnrollmentMutation,
  useVerifyTotpMutation,
} from "@/lib/queries/mfa";

type EnrollmentState =
  | { status: "idle" }
  | { status: "ready"; secret: string; methodId: string; otpauthUrl?: string | null };

export function MfaManagerCard() {
  const { success, error: errorToast } = useToast();
  const { data: methods = [], isLoading, refetch } = useMfaMethodsQuery(true);
  const revokeMutation = useRevokeMfaMethodMutation();
  const regenerateCodesMutation = useRegenerateRecoveryCodesMutation();
  const startEnrollment = useStartTotpEnrollmentMutation();
  const verifyEnrollment = useVerifyTotpMutation();

  const [enrollment, setEnrollment] = useState<EnrollmentState>({ status: "idle" });
  const [otpCode, setOtpCode] = useState("");
  const hasVerified = useMemo(() => methods.some((m) => !m.revoked_at && m.verified_at), [methods]);

  const handleStart = async () => {
    try {
      const res = await startEnrollment.mutateAsync("Authenticator");
      setEnrollment({ status: "ready", secret: res.secret, methodId: res.method_id, otpauthUrl: res.otpauth_url });
      success({ title: "TOTP enrollment started", description: "Scan the code and enter the 6-digit token." });
    } catch (error) {
      errorToast({ title: "Unable to start enrollment", description: error instanceof Error ? error.message : "Try again" });
    }
  };

  const handleVerify = async () => {
    if (enrollment.status !== "ready") return;
    try {
      await verifyEnrollment.mutateAsync({ method_id: enrollment.methodId, code: otpCode });
      setOtpCode("");
      setEnrollment({ status: "idle" });
      await refetch();
      success({ title: "MFA enabled", description: "TOTP verified successfully." });
    } catch (error) {
      errorToast({
        title: "Verification failed",
        description: error instanceof Error ? error.message : "Check the code and try again.",
      });
    }
  };

  const handleRevoke = async (id: string) => {
    try {
      await revokeMutation.mutateAsync(id);
      await refetch();
      success({ title: "MFA method revoked" });
    } catch (error) {
      errorToast({
        title: "Unable to revoke",
        description: error instanceof Error ? error.message : "Try again.",
      });
    }
  };

  const handleRegenerateCodes = async () => {
    try {
      const res = await regenerateCodesMutation.mutateAsync();
      success({
        title: "Recovery codes regenerated",
        description: res.codes.slice(0, 3).join(" · ") + (res.codes.length > 3 ? " …" : ""),
      });
    } catch (error) {
      errorToast({ title: "Failed to regenerate codes", description: error instanceof Error ? error.message : "" });
    }
  };

  return (
    <GlassPanel className="space-y-5">
      <SectionHeader
        eyebrow="Security"
        title="Multi-factor authentication"
        description="Add a TOTP factor, manage devices, and rotate recovery codes."
        actions={hasVerified ? <Badge variant="outline" className="border-green-500 text-green-500"><ShieldCheck className="mr-1 h-3 w-3" /> Enabled</Badge> : <Badge variant="outline"><ShieldOff className="mr-1 h-3 w-3" /> Disabled</Badge>}
      />

      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium">Enrolled methods</p>
            <p className="text-xs text-muted-foreground">TOTP methods that are verified and active.</p>
          </div>
          <Button size="sm" onClick={handleStart} disabled={startEnrollment.isPending}>
            {startEnrollment.isPending ? "Starting…" : "Add TOTP"}
          </Button>
        </div>

        <div className="space-y-2 rounded-md border border-border p-3">
          {isLoading ? (
            <p className="text-sm text-muted-foreground">Loading methods…</p>
          ) : methods.length === 0 ? (
            <p className="text-sm text-muted-foreground">No MFA methods yet. Add TOTP to protect your account.</p>
          ) : (
            methods.map((method) => (
              <div key={method.id} className="flex items-center justify-between rounded-md bg-muted/40 px-3 py-2 text-sm">
                <div className="space-y-0.5">
                  <div className="flex items-center gap-2">
                    <span className="font-medium">{method.label ?? method.method_type}</span>
                    {method.verified_at ? (
                      <Badge variant="outline" className="border-green-500 text-green-500">Verified</Badge>
                    ) : (
                      <Badge variant="secondary">Pending</Badge>
                    )}
                  </div>
                  <p className="text-xs text-muted-foreground">Last used: {method.last_used_at ?? "—"}</p>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleRevoke(method.id)}
                  disabled={revokeMutation.isPending}
                >
                  Revoke
                </Button>
              </div>
            ))
          )}
        </div>
      </div>

      {enrollment.status === "ready" ? (
        <div className="space-y-3 rounded-md border border-dashed p-3">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-sm font-medium">Verify TOTP</p>
              <p className="text-xs text-muted-foreground">Scan the secret below, then enter the 6-digit code.</p>
            </div>
            <Badge variant="secondary">Step 2 of 2</Badge>
          </div>
          <div className="rounded bg-muted px-3 py-2 font-mono text-sm">{enrollment.secret}</div>
          {enrollment.otpauthUrl ? (
            <p className="text-xs text-muted-foreground">QR not shown here—use the secret above or paste the otpauth URL into your authenticator.</p>
          ) : null}
          <div className="space-y-2">
            <Label htmlFor="otp">Code</Label>
            <Input
              id="otp"
              value={otpCode}
              inputMode="numeric"
              maxLength={8}
              onChange={(e) => setOtpCode(e.target.value)}
              placeholder="123456"
            />
            <div className="flex gap-2">
              <Button variant="ghost" onClick={() => setEnrollment({ status: "idle" })} size="sm">
                Cancel
              </Button>
              <Button onClick={handleVerify} size="sm" disabled={verifyEnrollment.isPending || otpCode.length < 6}>
                {verifyEnrollment.isPending ? "Verifying…" : "Verify"}
              </Button>
            </div>
          </div>
        </div>
      ) : null}

      <Separator />

      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <AlertCircle className="h-4 w-4" />
          <span>Rotate recovery codes after enabling MFA.</span>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={handleRegenerateCodes}
          disabled={regenerateCodesMutation.isPending}
        >
          {regenerateCodesMutation.isPending ? "Regenerating…" : "Regenerate recovery codes"}
        </Button>
      </div>
    </GlassPanel>
  );
}
