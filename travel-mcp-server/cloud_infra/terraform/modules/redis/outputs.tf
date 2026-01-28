output "id" {
  description = "Redis cache ID"
  value       = azurerm_redis_cache.this.id
}

output "hostname" {
  description = "Redis cache hostname"
  value       = azurerm_redis_cache.this.hostname
}

output "ssl_port" {
  description = "Redis SSL port"
  value       = azurerm_redis_cache.this.ssl_port
}

output "primary_access_key" {
  description = "Primary access key"
  value       = azurerm_redis_cache.this.primary_access_key
  sensitive   = true
}

output "primary_connection_string" {
  description = "Primary connection string"
  value       = azurerm_redis_cache.this.primary_connection_string
  sensitive   = true
}
