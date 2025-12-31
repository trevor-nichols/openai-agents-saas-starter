# Chaos Testing Stub

This folder provides a minimal harness stub for chaos/fault-injection testing.
It is intentionally manual so downstream deployments can wire it to their own
staging environment and injector tooling (toxiproxy, Kubernetes fault tools,
service mesh faults, etc.).

## Why a stub?
- The starter repo does not ship a staging environment.
- Chaos tests are inherently destructive and should never run on PRs.
- This scaffold documents how to add real fault-injection when you deploy.

## Manual run (dry-run connectivity check)
```
CHAOS_BASE_URL=https://api.example.com \
CHAOS_DRY_RUN=true \
./tools/chaos/run_chaos_stub.sh
```

## Wiring a real injector (example)
1. Stand up a fault injector (e.g., toxiproxy) in your environment.
2. Set `CHAOS_INJECTOR=toxiproxy`.
3. Implement scenario logic inside `run_chaos_stub.sh` or replace it with a
   proper script that configures latency, drops, or restarts.

## Suggested scenarios
- Redis latency or disconnect.
- Postgres restart or connection failure.
- HTTP dependency timeout.
- Slow outbound network to third-party APIs.
