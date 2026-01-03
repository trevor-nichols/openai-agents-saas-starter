variable "project_name" {
  type        = string
  description = "Base project name used for resource naming."
}

variable "environment" {
  type        = string
  description = "Deployment environment (dev/staging/prod)."
}

variable "region" {
  type        = string
  description = "AWS region for all resources."
  default     = "us-east-1"
}

variable "vpc_cidr" {
  type        = string
  description = "CIDR block for the VPC."
  default     = "10.20.0.0/16"
}

variable "api_image" {
  type        = string
  description = "Container image for the API service."
}

variable "web_image" {
  type        = string
  description = "Container image for the web app."
}

variable "api_base_url" {
  type        = string
  description = "Optional public API base URL (e.g., https://api.example.com). Defaults to the API ALB URL."
  default     = ""
}

variable "app_public_url" {
  type        = string
  description = "Optional public web URL (e.g., https://app.example.com). Defaults to the web ALB URL."
  default     = ""
}

variable "secrets_provider" {
  type        = string
  description = "Secrets provider used by the API service (SECRETS_PROVIDER). Default posture assumes aws_sm."
  default     = "aws_sm"
}

variable "aws_sm_signing_secret_arn" {
  type        = string
  description = "Secrets Manager ARN for the signing secret used by service-account issuance."
  default     = ""
  validation {
    condition = (
      var.secrets_provider != "aws_sm"
      || length(trimspace(var.aws_sm_signing_secret_arn)) > 0
      || contains(keys(var.api_env), "AWS_SM_SIGNING_SECRET_ARN")
      || contains(keys(var.api_secrets), "AWS_SM_SIGNING_SECRET_ARN")
    )
    error_message = "aws_sm_signing_secret_arn is required when secrets_provider=aws_sm (or provide AWS_SM_SIGNING_SECRET_ARN via api_env/api_secrets)."
  }
}

variable "auth_key_secret_arn" {
  type        = string
  description = "Secrets Manager ARN for the Ed25519 keyset JSON (AUTH_KEY_SECRET_NAME)."
  default     = ""
  validation {
    condition = (
      (trimspace(var.auth_key_storage_provider) != "" ? var.auth_key_storage_provider : var.secrets_provider) != "aws_sm"
      || length(trimspace(var.auth_key_secret_arn)) > 0
      || length(trimspace(var.auth_key_secret_name)) > 0
    )
    error_message = "auth_key_secret_arn or auth_key_secret_name is required when auth_key_storage_provider=aws_sm so IAM can grant keyset secret access."
  }
}

variable "auth_key_storage_provider" {
  type        = string
  description = "Secrets provider used for key storage (AUTH_KEY_STORAGE_PROVIDER). Defaults to secrets_provider."
  default     = ""
}

variable "auth_key_secret_name" {
  type        = string
  description = "Secret-manager key/path for the Ed25519 keyset JSON (AUTH_KEY_SECRET_NAME)."
  default     = ""
  validation {
    condition = (
      (trimspace(var.auth_key_storage_provider) != "" ? var.auth_key_storage_provider : var.secrets_provider) == "aws_sm"
      ? true
      : (
        length(trimspace(var.auth_key_secret_name)) > 0
        || contains(keys(var.api_env), "AUTH_KEY_SECRET_NAME")
        || contains(keys(var.api_secrets), "AUTH_KEY_SECRET_NAME")
      )
    )
    error_message = "auth_key_secret_name is required when auth_key_storage_provider is not aws_sm (or provide AUTH_KEY_SECRET_NAME via api_env/api_secrets)."
  }
}

variable "registry_server" {
  type        = string
  description = "Container registry server hostname (ghcr.io, <registry>.azurecr.io)."
  default     = ""
}

variable "registry_username" {
  type        = string
  description = "Container registry username (required when registry_server is set)."
  default     = ""
  validation {
    condition     = var.registry_server == "" || length(trimspace(var.registry_username)) > 0
    error_message = "registry_username is required when registry_server is set."
  }
}

variable "registry_password" {
  type        = string
  description = "Container registry password/token (required when registry_server is set)."
  default     = ""
  sensitive   = true
  validation {
    condition     = var.registry_server == "" || length(trimspace(var.registry_password)) > 0
    error_message = "registry_password is required when registry_server is set."
  }
}

variable "api_cpu" {
  type        = number
  description = "CPU units for the API task definition."
  default     = 512
}

variable "api_memory" {
  type        = number
  description = "Memory (MiB) for the API task definition."
  default     = 1024
}

variable "web_cpu" {
  type        = number
  description = "CPU units for the web task definition."
  default     = 512
}

variable "web_memory" {
  type        = number
  description = "Memory (MiB) for the web task definition."
  default     = 1024
}

variable "api_desired_count" {
  type        = number
  description = "Desired task count for the API service."
  default     = 1
}

variable "web_desired_count" {
  type        = number
  description = "Desired task count for the web service."
  default     = 1
}

variable "db_instance_class" {
  type        = string
  description = "RDS instance class for Postgres."
  default     = "db.t4g.micro"
}

variable "db_allocated_storage" {
  type        = number
  description = "Allocated storage (GiB) for Postgres."
  default     = 20
}

variable "db_backup_retention_days" {
  type        = number
  description = "Backup retention (days) for Postgres."
  default     = 7
}

variable "db_storage_encrypted" {
  type        = bool
  description = "Enable storage encryption at rest for Postgres."
  default     = true
}

variable "db_deletion_protection" {
  type        = bool
  description = "Enable deletion protection for Postgres."
  default     = true
}

variable "db_skip_final_snapshot" {
  type        = bool
  description = "Skip final snapshot on destroy (useful for dev only)."
  default     = false
}

variable "db_publicly_accessible" {
  type        = bool
  description = "Expose Postgres to the public internet (not recommended)."
  default     = false
}

variable "db_name" {
  type        = string
  description = "Postgres database name."
  default     = "agent_app"
}

variable "db_username" {
  type        = string
  description = "Postgres master username."
  default     = "agent_admin"
}

variable "db_password" {
  type        = string
  description = "Postgres master password."
  sensitive   = true
}

variable "redis_node_type" {
  type        = string
  description = "ElastiCache node type."
  default     = "cache.t4g.micro"
}

variable "redis_transit_encryption_enabled" {
  type        = bool
  description = "Enable in-transit encryption (TLS) for Redis."
  default     = true
}

variable "redis_at_rest_encryption_enabled" {
  type        = bool
  description = "Enable at-rest encryption for Redis."
  default     = true
}

variable "redis_require_auth_token" {
  type        = bool
  description = "Require a Redis AUTH token (recommended)."
  default     = true
}

variable "redis_auth_token" {
  type        = string
  description = "Redis AUTH token (required when redis_require_auth_token=true)."
  sensitive   = true
  default     = ""
  validation {
    condition     = var.redis_require_auth_token ? length(var.redis_auth_token) > 0 : true
    error_message = "redis_auth_token must be set when redis_require_auth_token=true."
  }
}

variable "storage_bucket_name" {
  type        = string
  description = "Storage bucket name for object storage."
}

variable "storage_provider" {
  type        = string
  description = "Storage provider for the API service (STORAGE_PROVIDER)."
  default     = "s3"
  validation {
    condition     = var.storage_provider == "s3"
    error_message = "storage_provider must be \"s3\" for the AWS blueprint."
  }
}

variable "create_s3_bucket" {
  type        = bool
  description = "Whether to manage the S3 bucket in this stack."
  default     = true
}

variable "s3_block_public_access" {
  type        = bool
  description = "Block all public access to the S3 bucket."
  default     = true
}

variable "s3_enable_encryption" {
  type        = bool
  description = "Enable default server-side encryption for the S3 bucket."
  default     = true
}

variable "s3_kms_key_id" {
  type        = string
  description = "Optional KMS key ID for S3 bucket encryption (defaults to SSE-S3)."
  default     = ""
}

variable "s3_enable_versioning" {
  type        = bool
  description = "Enable S3 bucket versioning."
  default     = true
}

variable "enable_https" {
  type        = bool
  description = "Whether to enable HTTPS listeners on the ALBs."
  default     = true
}

variable "acm_certificate_arn" {
  type        = string
  description = "ACM certificate ARN for HTTPS. Required when enable_https=true."
  default     = null
  validation {
    condition     = var.enable_https ? length(trimspace(coalesce(var.acm_certificate_arn, ""))) > 0 : true
    error_message = "acm_certificate_arn must be set when enable_https=true."
  }
}

variable "api_env" {
  type        = map(string)
  description = "Additional environment variables for the API container."
  default     = {}
  validation {
    condition = (
      !contains(keys(var.api_env), "DATABASE_URL")
      && !contains(keys(var.api_env), "REDIS_URL")
    )
    error_message = "DATABASE_URL and REDIS_URL must be provided via api_secrets, not api_env."
  }
}

variable "web_env" {
  type        = map(string)
  description = "Additional environment variables for the web container."
  default     = {}
}

variable "api_secrets" {
  type        = map(string)
  description = "Map of API env var name to AWS Secrets Manager secret ARN."
  default = {
    DATABASE_URL = ""
    REDIS_URL    = ""
  }
  validation {
    condition = (
      length(trimspace(lookup(var.api_secrets, "DATABASE_URL", ""))) > 0
      && length(trimspace(lookup(var.api_secrets, "REDIS_URL", ""))) > 0
    )
    error_message = "api_secrets must provide DATABASE_URL and REDIS_URL secret ARNs for production deployments."
  }
}

variable "web_secrets" {
  type        = map(string)
  description = "Map of web env var name to AWS Secrets Manager secret ARN."
  default     = {}
}
