resource "azurerm_redis_cache" "main" {
  name                = "redis-llm-gateway-${var.environment}-${var.name_suffix}"
  location            = var.location
  resource_group_name = var.resource_group_name
  capacity            = var.capacity
  family              = var.family
  sku_name            = var.sku_name
  non_ssl_port_enabled = false
  minimum_tls_version = "1.2"
  tags                = var.tags

  redis_configuration {
    maxmemory_policy = "allkeys-lru"
  }
}
