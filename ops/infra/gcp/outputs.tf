output "api_url" {
  value       = google_cloud_run_v2_service.api.uri
  description = "Base URL for the API service."
}

output "web_url" {
  value       = google_cloud_run_v2_service.web.uri
  description = "Base URL for the web service."
}

output "database_endpoint" {
  value       = google_sql_database_instance.main.private_ip_address
  description = "Postgres endpoint hostname."
}

output "redis_endpoint" {
  value       = google_redis_instance.main.host
  description = "Redis endpoint hostname."
}

output "storage_bucket" {
  value       = google_storage_bucket.main.name
  description = "Storage bucket name."
}
