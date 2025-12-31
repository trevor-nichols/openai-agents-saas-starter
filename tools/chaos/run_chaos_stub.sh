#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${CHAOS_BASE_URL:-}"
SCENARIO="${CHAOS_SCENARIO:-redis-latency}"
DRY_RUN="${CHAOS_DRY_RUN:-true}"
INJECTOR="${CHAOS_INJECTOR:-none}"

if [ -z "${BASE_URL}" ]; then
  echo "CHAOS_BASE_URL is required (example: https://api.example.com)." >&2
  exit 1
fi

echo "Chaos stub"
echo "- base_url=${BASE_URL}"
echo "- scenario=${SCENARIO}"
echo "- dry_run=${DRY_RUN}"
echo "- injector=${INJECTOR}"

if [ "${DRY_RUN}" = "true" ]; then
  echo "Running dry-run health check..."
  if ! curl -fsS "${BASE_URL%/}/health" >/dev/null 2>&1; then
    echo "Health check failed for ${BASE_URL%/}/health" >&2
    exit 2
  fi
  echo "Dry-run complete. No faults injected."
  exit 0
fi

if [ "${INJECTOR}" = "none" ]; then
  echo "No chaos injector configured. This is a stub harness." >&2
  echo "Set CHAOS_INJECTOR=toxiproxy and implement the scenario logic in tools/chaos." >&2
  exit 3
fi

echo "Injector '${INJECTOR}' not implemented yet." >&2
exit 4
