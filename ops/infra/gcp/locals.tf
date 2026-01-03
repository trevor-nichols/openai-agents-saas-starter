locals {
  name_prefix = "${var.project_name}-${var.environment}"

  api_container_port        = 8000
  web_container_port        = 3000
  secrets_provider          = trimspace(var.secrets_provider)
  auth_key_storage_provider = trimspace(var.auth_key_storage_provider) != "" ? var.auth_key_storage_provider : local.secrets_provider

  worker_enabled = var.enable_worker_service
  worker_image   = trimspace(var.worker_image) != "" ? var.worker_image : var.api_image

  network_name               = "${local.name_prefix}-vpc"
  subnet_name                = "${local.name_prefix}-subnet"
  vpc_connector_name         = "${local.name_prefix}-vpc-connector"
  private_service_range_name = "${local.name_prefix}-svc-range"
  redis_instance_name        = "${local.name_prefix}-redis"
  storage_location           = trimspace(var.storage_location) != "" ? var.storage_location : var.region

  api_base_url      = trimspace(var.api_base_url)
  app_public_url    = trimspace(var.app_public_url)
  api_base_host     = element(split("/", replace(replace(local.api_base_url, "https://", ""), "http://", "")), 0)
  api_allowed_hosts = join(",", compact([local.api_base_host, "127.0.0.1", "localhost"]))

  api_env_base = merge(
    {
      PORT                      = tostring(local.api_container_port)
      ENVIRONMENT               = var.environment
      SECRETS_PROVIDER          = local.secrets_provider
      AUTH_KEY_STORAGE_BACKEND  = "secret-manager"
      AUTH_KEY_STORAGE_PROVIDER = local.auth_key_storage_provider
      STORAGE_PROVIDER          = var.storage_provider
      GCS_BUCKET                = var.storage_bucket_name
      GCS_PROJECT_ID            = var.project_id
      APP_PUBLIC_URL            = local.app_public_url
      ALLOWED_HOSTS             = local.api_allowed_hosts
      ALLOWED_ORIGINS           = local.app_public_url
    },
    (local.secrets_provider == "gcp_sm" || local.auth_key_storage_provider == "gcp_sm") ? {
      GCP_SM_PROJECT_ID = var.project_id
    } : {},
    local.secrets_provider == "gcp_sm" ? {
      GCP_SM_SIGNING_SECRET_NAME = var.gcp_sm_signing_secret_name
    } : {},
    trimspace(var.auth_key_secret_name) != "" ? { AUTH_KEY_SECRET_NAME = var.auth_key_secret_name } : {},
    local.worker_enabled ? {
      ENABLE_BILLING_RETRY_WORKER   = "false"
      ENABLE_BILLING_STREAM_REPLAY  = "false"
      BILLING_RETRY_DEPLOYMENT_MODE = "dedicated"
    } : {}
  )

  worker_env_base = merge(
    local.api_env_base,
    {
      ENABLE_BILLING_RETRY_WORKER   = "true"
      ENABLE_BILLING_STREAM_REPLAY  = "true"
      BILLING_RETRY_DEPLOYMENT_MODE = "dedicated"
    }
  )

  web_env_base = {
    PORT         = tostring(local.web_container_port)
    API_BASE_URL = local.api_base_url
  }

  api_env_combined    = merge(local.api_env_base, var.api_env)
  web_env_combined    = merge(local.web_env_base, var.web_env)
  worker_env_combined = local.worker_env_base

  api_env_list    = [for key, value in local.api_env_combined : { name = key, value = value }]
  web_env_list    = [for key, value in local.web_env_combined : { name = key, value = value }]
  worker_env_list = [for key, value in local.worker_env_combined : { name = key, value = value }]

  api_secret_refs = {
    for key, raw in var.api_secrets : key => {
      normalized = startswith(trimspace(raw), "projects/") ? trimspace(raw) : "projects/${var.project_id}/secrets/${trimspace(raw)}"
      secret     = length(split("/versions/", normalized)) > 1 ? element(split("/versions/", normalized), 0) : normalized
      version    = length(split("/versions/", normalized)) > 1 ? element(split("/versions/", normalized), 1) : "latest"
    }
    if length(trimspace(raw)) > 0
  }
  web_secret_refs = {
    for key, raw in var.web_secrets : key => {
      normalized = startswith(trimspace(raw), "projects/") ? trimspace(raw) : "projects/${var.project_id}/secrets/${trimspace(raw)}"
      secret     = length(split("/versions/", normalized)) > 1 ? element(split("/versions/", normalized), 0) : normalized
      version    = length(split("/versions/", normalized)) > 1 ? element(split("/versions/", normalized), 1) : "latest"
    }
    if length(trimspace(raw)) > 0
  }

  api_secret_list = [
    for key, ref in local.api_secret_refs : {
      name    = key
      secret  = ref.secret
      version = ref.version
    }
  ]

  web_secret_list = [
    for key, ref in local.web_secret_refs : {
      name    = key
      secret  = ref.secret
      version = ref.version
    }
  ]

  worker_secret_list = local.api_secret_list
  service_account_id = substr(regexreplace(lower("sa-${local.name_prefix}"), "[^a-z0-9-]", ""), 0, 30)

  required_project_services = toset([
    "compute.googleapis.com",
    "iam.googleapis.com",
    "redis.googleapis.com",
    "run.googleapis.com",
    "secretmanager.googleapis.com",
    "servicenetworking.googleapis.com",
    "sqladmin.googleapis.com",
    "storage.googleapis.com",
    "vpcaccess.googleapis.com",
  ])
}
