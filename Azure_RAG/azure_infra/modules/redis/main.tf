resource "azurerm_redis_cache" "this" {
  name                = var.name
  resource_group_name = var.resource_group_name
  location            = var.location
  capacity            = var.capacity
  family              = var.sku_name == "Premium" ? "P" : "C"
  sku_name            = var.sku_name

  enable_non_ssl_port = false
  minimum_tls_version = "1.2"
  public_network_access_enabled = true

  redis_configuration {
    enable_authentication = true
  }

  tags = var.tags
}
