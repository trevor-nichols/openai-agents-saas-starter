# Kubernetes Hosting Guide

This guide documents the Kubernetes deployment option for the starter. The reference Helm chart
lives in `ops/charts/starter`.

## Reference Chart

The chart will deploy:
- API Deployment + Service
- Web Deployment + Service
- Optional worker Deployment
- Ingress with TLS
- Horizontal Pod Autoscaler (API/Web)
- External Secrets Operator integration (default)

## Prerequisites

- Kubernetes 1.27+ (managed recommended)
- Ingress controller (nginx, traefik, or equivalent)
- TLS automation (cert-manager recommended)
- External Secrets Operator (default secrets path)
- Managed Postgres and Redis endpoints (recommended)

## Values Contract (core)

```yaml
api:
  image: "registry/app-api:tag"
  env: {}
  secrets: {}
  secretName: ""
web:
  image: "registry/app-web:tag"
  env: {}
  secrets: {}
  secretName: ""
worker:
  enabled: false
  image: "registry/app-api:tag"
  env: {}
  secrets: {}
  secretName: ""
ingress:
  enabled: true
  className: nginx
  hosts:
    - host: app.example.com
  tls:
    - secretName: app-tls
      hosts:
        - app.example.com
  apiHosts: []
  apiTls: []
ingressPaths:
  api: /api
  web: /
  apiHost: /
externalSecrets:
  enabled: true
  secretStoreRef:
    name: platform-secrets
    kind: ClusterSecretStore
  api:
    data: {}
  web:
    data: {}
  worker:
    data: {}
autoscaling:
  enabled: true
  targetCPUUtilizationPercentage: 80
  api:
    minReplicas: 2
    maxReplicas: 10
  web:
    minReplicas: 2
    maxReplicas: 10
```

### Secrets mapping
- **External Secrets (default):** set `externalSecrets.enabled=true` and map secrets under
  `externalSecrets.api.data` / `externalSecrets.web.data` / `externalSecrets.worker.data`.
  Keys become env var names; values are provider secret identifiers.
  Ensure `externalSecrets.secretStoreRef` points at a valid SecretStore/ClusterSecretStore.
- **Static Secrets (fallback):** set `externalSecrets.enabled=false` and provide
  `api.secrets` / `web.secrets` / `worker.secrets` as **env var name → secret value**.
- Override secret names with `api.secretName` / `web.secretName` / `worker.secretName` if needed.

Example (External Secrets):

```yaml
externalSecrets:
  api:
    data:
      DATABASE_URL: "prod/database_url"
      REDIS_URL: "prod/redis_url"
  web:
    data:
      API_BASE_URL: "prod/api_base_url"
```

## Quickstart (non-technical)

1. **Build + publish images** using `.github/workflows/build-images.yml`.
2. **Provision Postgres + Redis** (managed services recommended).
3. **Install External Secrets Operator** and configure a `SecretStore` or `ClusterSecretStore`.
4. **Create ExternalSecrets** for `DATABASE_URL` and `REDIS_URL` (keys should match env var names).
5. **Install the chart** with your values file:
   ```bash
   helm upgrade --install starter ops/charts/starter -f values.prod.yaml
   ```
6. **Run migrations** (`starter-console release db`).
7. **Verify health**: `/health/ready` (API) and `/api/health/ready` (web).

## Secrets Strategy

Default approach is External Secrets Operator:
- Map cloud secrets into Kubernetes Secrets.
- Use those Secrets for `DATABASE_URL`, `REDIS_URL`, and any provider keys.

Optional path:
- Secrets Store CSI Driver for file-mounted secrets (documented as advanced).

## Resources + Autoscaling

- Default CPU/memory requests + limits live under `api.resources`, `web.resources`, `worker.resources`.
- Enable HPA with `autoscaling.enabled=true`; API/web have independent min/max settings.

## Environment Variables (minimal)

### API
- `ENVIRONMENT`
- `APP_PUBLIC_URL`
- `SECRETS_PROVIDER` (aws_sm/azure_kv/gcp_sm/vault/infisical)
- `AUTH_KEY_STORAGE_BACKEND=secret-manager`
- `AUTH_KEY_STORAGE_PROVIDER`
- `AUTH_KEY_SECRET_NAME`
- `STORAGE_PROVIDER` and provider-specific settings (S3/Azure Blob/GCS/MinIO)

### Web
- `API_BASE_URL`

## Ingress + TLS

- Use cert-manager to request and renew certificates.
- Ingress should route `ingressPaths.web` (default `/`) to web and `ingressPaths.api` (default `/api`) to the web app BFF.
- If you want a separate API hostname, set `ingress.apiHosts` (and optionally `ingress.apiTls`) to
  route `ingressPaths.apiHost` (default `/`) directly to the API service.

## Billing Worker Topology

When running more than one API replica, move billing retries into a dedicated worker:
- API: `ENABLE_BILLING_RETRY_WORKER=false`, `ENABLE_BILLING_STREAM_REPLAY=false`
- Worker: `ENABLE_BILLING_RETRY_WORKER=true`, `ENABLE_BILLING_STREAM_REPLAY=true`, `BILLING_RETRY_DEPLOYMENT_MODE=dedicated`
The Helm chart auto-disables API retries and stream replay when `worker.enabled=true` unless you
explicitly set `ENABLE_BILLING_RETRY_WORKER` or `ENABLE_BILLING_STREAM_REPLAY` in `api.env`.

## Migrations

Run migrations as a pre-deploy job or one-off task:

```bash
starter-console release db
```

## Rollback Notes

- **Fast rollback**: revert chart values to the previous image tags.
- **Infrastructure rollback**: managed data services should not be destroyed by chart changes.

## Ops Checklist

- [ ] SecretStore or ClusterSecretStore is configured and healthy.
- [ ] `DATABASE_URL` and `REDIS_URL` secrets are present.
- [ ] Ingress and TLS are configured and reachable.
- [ ] Migrations ran successfully.
- [ ] Health checks are green for API and web.
