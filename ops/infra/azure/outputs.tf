output "api_url" {
  value       = "https://${azurerm_container_app.api.ingress[0].fqdn}"
  description = "Base URL for the API container app."
}

output "web_url" {
  value       = "https://${azurerm_container_app.web.ingress[0].fqdn}"
  description = "Base URL for the web container app."
}

output "postgres_fqdn" {
  value       = azurerm_postgresql_flexible_server.main.fqdn
  description = "Postgres server hostname."
}

output "redis_hostname" {
  value       = azurerm_redis_cache.main.hostname
  description = "Redis hostname."
}

output "storage_account" {
  value       = azurerm_storage_account.main.name
  description = "Storage account name."
}

output "key_vault_uri" {
  value       = azurerm_key_vault.main.vault_uri
  description = "Key Vault URI."
}
