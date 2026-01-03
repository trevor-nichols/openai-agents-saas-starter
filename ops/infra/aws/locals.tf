locals {
  name_prefix               = "${var.project_name}-${var.environment}"
  api_container_port        = 8000
  web_container_port        = 3000
  registry_server           = trimspace(var.registry_server)
  registry_enabled          = local.registry_server != ""
  secrets_provider          = trimspace(var.secrets_provider)
  auth_key_storage_provider = trimspace(var.auth_key_storage_provider) != "" ? var.auth_key_storage_provider : local.secrets_provider

  api_scheme = var.enable_https ? "https" : "http"
  api_url    = "${local.api_scheme}://${aws_lb.api.dns_name}"
  web_url    = "${local.api_scheme}://${aws_lb.web.dns_name}"

  api_base_url             = trimspace(var.api_base_url)
  app_public_url           = trimspace(var.app_public_url)
  api_base_url_effective   = local.api_base_url != "" ? local.api_base_url : local.api_url
  app_public_url_effective = local.app_public_url != "" ? local.app_public_url : local.web_url

  api_base_host = element(
    split("/", replace(replace(local.api_base_url_effective, "https://", ""), "http://", "")),
    0
  )
  api_allowed_hosts = join(",", compact([local.api_base_host, "127.0.0.1", "localhost"]))

  auth_key_secret_arn_effective = local.auth_key_storage_provider == "aws_sm" ? (
    trimspace(var.auth_key_secret_arn) != "" ? (
      startswith(trimspace(var.auth_key_secret_arn), "arn:")
      ? trimspace(var.auth_key_secret_arn)
      : "arn:aws:secretsmanager:${var.region}:${data.aws_caller_identity.current.account_id}:secret:${trimspace(var.auth_key_secret_arn)}*"
      ) : (
      trimspace(var.auth_key_secret_name) != "" ? (
        startswith(trimspace(var.auth_key_secret_name), "arn:")
        ? trimspace(var.auth_key_secret_name)
        : "arn:aws:secretsmanager:${var.region}:${data.aws_caller_identity.current.account_id}:secret:${trimspace(var.auth_key_secret_name)}*"
      ) : ""
    )
  ) : ""

  aws_secret_arns = compact(concat(
    local.secrets_provider == "aws_sm" ? [var.aws_sm_signing_secret_arn] : [],
    local.auth_key_secret_arn_effective != "" ? [local.auth_key_secret_arn_effective] : []
  ))
  secret_arns           = compact(concat(values(var.api_secrets), values(var.web_secrets), local.aws_secret_arns))
  auth_key_secret_value = trimspace(var.auth_key_secret_name) != "" ? var.auth_key_secret_name : var.auth_key_secret_arn

  api_env_base = merge(
    {
      PORT                      = tostring(local.api_container_port)
      ENVIRONMENT               = var.environment
      APP_PUBLIC_URL            = local.app_public_url_effective
      SECRETS_PROVIDER          = local.secrets_provider
      AWS_REGION                = var.region
      AUTH_KEY_STORAGE_BACKEND  = "secret-manager"
      AUTH_KEY_STORAGE_PROVIDER = local.auth_key_storage_provider
      STORAGE_PROVIDER          = var.storage_provider
      S3_BUCKET                 = var.storage_bucket_name
      S3_REGION                 = var.region
      ALLOWED_HOSTS             = local.api_allowed_hosts
      ALLOWED_ORIGINS           = local.app_public_url_effective
    },
    local.secrets_provider == "aws_sm" ? { AWS_SM_SIGNING_SECRET_ARN = var.aws_sm_signing_secret_arn } : {},
    local.auth_key_secret_value != "" ? { AUTH_KEY_SECRET_NAME = local.auth_key_secret_value } : {}
  )

  web_env_base = {
    PORT         = tostring(local.web_container_port)
    API_BASE_URL = local.api_base_url_effective
  }

  api_env_combined = merge(local.api_env_base, var.api_env)
  web_env_combined = merge(local.web_env_base, var.web_env)

  api_env_list = [for key, value in local.api_env_combined : { name = key, value = value }]
  web_env_list = [for key, value in local.web_env_combined : { name = key, value = value }]

  api_secret_list = [
    for key, value in var.api_secrets : { name = key, valueFrom = value }
    if length(trimspace(value)) > 0
  ]
  web_secret_list = [for key, value in var.web_secrets : { name = key, valueFrom = value }]
}
