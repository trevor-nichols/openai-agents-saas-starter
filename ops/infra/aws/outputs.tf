output "api_url" {
  value       = local.api_url
  description = "Base URL for the API ALB."
}

output "web_url" {
  value       = local.web_url
  description = "Base URL for the web ALB."
}

output "database_endpoint" {
  value       = aws_db_instance.main.address
  description = "Postgres endpoint hostname."
}

output "redis_endpoint" {
  value       = aws_elasticache_replication_group.main.primary_endpoint_address
  description = "Redis endpoint hostname."
}

output "storage_bucket" {
  value       = var.storage_bucket_name
  description = "Storage bucket name."
}
