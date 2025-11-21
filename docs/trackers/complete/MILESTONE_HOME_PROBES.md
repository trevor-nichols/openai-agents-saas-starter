# Milestone: Home TUI Provider-Aware Probes

**Owner:** CLI  
**Created:** 2025-11-21  
**Goal:** Make the home/doctor probes declarative and provider-aware so adding secrets or billing providers is data-only (no refactors), while keeping the TUI signal high for non‑enabled features.

## Deliverables
- Probe registry + context so probes are configured, ordered, and extensible without touching the runner.
- Provider-aware `secrets` probe (Vault, Infisical, AWS SM, Azure KV; skips cleanly when unconfigured/unknown).
- Billing-aware probe that skips when billing/Stripe isn’t enabled instead of warning noisily.
- Updated unit tests covering provider/billing branches and registry ordering.
- Docs updated to describe new probe behavior and extensibility.

## Work Plan & Status
- [x] Design freeze: finalize ProbeSpec/ProbeContext shapes and registry contract.
- [x] Implement registry + runner wiring (doctor uses registry for probe execution).
- [x] Implement `secrets_probe` with provider dispatch (Vault/Infisical/AWS SM/Azure KV) and SKIP when not configured.
- [x] Implement `billing_probe` with Stripe awareness and SKIP when billing disabled; tighten Stripe error semantics.
- [x] Update tests: table-driven coverage for secrets/billing probes; runner maintains ordering; adjust fixtures as needed.
- [x] Docs: snapshot updates and brief note on probe extensibility/TUI expectations.

## Notes
- Respect existing “safe env” warn-only semantics.
- Keep `ProbeResult` contract stable; add category metadata via ProbeSpec for future UI grouping.
- Avoid noisy WARNs for features the operator hasn’t enabled.

### Docs quick note
- Home/doctor probes now run from `probes/registry.py` with provider-aware `secrets` and billing-aware `billing` probes. Optional features SKIP when unconfigured, keeping the TUI clean. Future providers are added by appending a `ProbeSpec`.
