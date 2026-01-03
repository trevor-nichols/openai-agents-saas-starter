# Starter Helm Chart

This chart deploys the API + web containers (and an optional worker) onto Kubernetes.

## Install

```bash
helm upgrade --install starter ops/charts/starter \
  -f values.prod.yaml \
  --set api.image=ghcr.io/org/starter-api:prod \
  --set web.image=ghcr.io/org/starter-web:prod
```

## Values highlights

- `api.image`, `web.image`, `worker.image` (required when worker enabled)
- `api.env`, `web.env`, `worker.env` for plain env vars
- `api.secretName`, `web.secretName`, `worker.secretName` to override secret names
- `api.secrets`, `web.secrets`, `worker.secrets` map **env var name → secret value** (static secrets only)
- `externalSecrets.*.data` map **env var name → provider secret key** (default)
- `ingress.*` and `ingressPaths.*` for Ingress config
- `ingress.apiHosts` / `ingress.apiTls` for an optional API hostname (server-to-server)
- `autoscaling.*` for HPA (CPU) on API + web

## Secrets strategy

Default: External Secrets Operator. Provide `externalSecrets.*.data` for API/web/worker secrets. Keys
become env var names, values are provider secret identifiers.
If you disable External Secrets (`externalSecrets.enabled=false`), the chart will create standard
Kubernetes Secrets using
`api.secrets` / `web.secrets` / `worker.secrets` values (base64 encoded). Keys become env var names.
