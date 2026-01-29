terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
  }
}

variable "resource_group_name" {
  type        = string
  description = "Resource group name"
}

variable "location" {
  type        = string
  description = "Azure region"
}

variable "resource_prefix" {
  type        = string
  description = "Prefix for resource names"
}

variable "tags" {
  type        = map(string)
  description = "Resource tags"
}

variable "sku_name" {
  type        = string
  default     = "Basic"
  description = "Redis SKU (Basic, Standard, Premium)"
}

variable "capacity" {
  type        = number
  default     = 0
  description = "Redis cache capacity (0 = 250MB for Basic)"
}

# Azure Cache for Redis
resource "azurerm_redis_cache" "main" {
  name                          = "${var.resource_prefix}-redis"
  location                      = var.location
  resource_group_name           = var.resource_group_name
  capacity                      = var.capacity
  family                        = var.sku_name == "Premium" ? "P" : "C"
  sku_name                      = var.sku_name
  non_ssl_port_enabled          = false
  minimum_tls_version           = "1.2"
  public_network_access_enabled = true
  tags                          = var.tags
}

output "hostname" {
  value = azurerm_redis_cache.main.hostname
}

output "port" {
  value = azurerm_redis_cache.main.ssl_port
}

output "primary_access_key" {
  value     = azurerm_redis_cache.main.primary_access_key
  sensitive = true
}

output "connection_string" {
  value     = azurerm_redis_cache.main.primary_connection_string
  sensitive = true
}

output "redis_url" {
  value     = "rediss://:${azurerm_redis_cache.main.primary_access_key}@${azurerm_redis_cache.main.hostname}:${azurerm_redis_cache.main.ssl_port}"
  sensitive = true
}
