resource "azurerm_private_dns_zone" "postgres" {
  count               = var.enable_private_networking ? 1 : 0
  name                = "privatelink.postgres.database.azure.com"
  resource_group_name = azurerm_resource_group.main.name
}

resource "azurerm_private_dns_zone_virtual_network_link" "postgres" {
  count                 = var.enable_private_networking ? 1 : 0
  name                  = "${local.name_prefix}-postgres"
  resource_group_name   = azurerm_resource_group.main.name
  private_dns_zone_name = azurerm_private_dns_zone.postgres[0].name
  virtual_network_id    = azurerm_virtual_network.main[0].id
}

resource "azurerm_private_dns_zone" "redis" {
  count               = var.enable_private_networking ? 1 : 0
  name                = "privatelink.redis.cache.windows.net"
  resource_group_name = azurerm_resource_group.main.name
}

resource "azurerm_private_dns_zone_virtual_network_link" "redis" {
  count                 = var.enable_private_networking ? 1 : 0
  name                  = "${local.name_prefix}-redis"
  resource_group_name   = azurerm_resource_group.main.name
  private_dns_zone_name = azurerm_private_dns_zone.redis[0].name
  virtual_network_id    = azurerm_virtual_network.main[0].id
}
