output "hostname" {
  description = "Redis hostname"
  value       = azurerm_redis_cache.main.hostname
}

output "ssl_port" {
  description = "Redis SSL port"
  value       = azurerm_redis_cache.main.ssl_port
}

output "primary_access_key" {
  description = "Redis primary access key"
  value       = azurerm_redis_cache.main.primary_access_key
  sensitive   = true
}

output "connection_string" {
  description = "Redis connection string"
  value       = azurerm_redis_cache.main.primary_connection_string
  sensitive   = true
}

output "id" {
  description = "Redis ID"
  value       = azurerm_redis_cache.main.id
}

output "name" {
  description = "Redis name"
  value       = azurerm_redis_cache.main.name
}
