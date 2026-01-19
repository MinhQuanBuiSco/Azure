output "postgres_id" {
  description = "PostgreSQL server ID"
  value       = azurerm_postgresql_flexible_server.postgres.id
}

output "postgres_fqdn" {
  description = "PostgreSQL server FQDN"
  value       = azurerm_postgresql_flexible_server.postgres.fqdn
}

output "postgres_admin_username" {
  description = "PostgreSQL admin username"
  value       = azurerm_postgresql_flexible_server.postgres.administrator_login
  sensitive   = true
}

output "database_name" {
  description = "Database name"
  value       = azurerm_postgresql_flexible_server_database.fraud_detection.name
}

output "redis_id" {
  description = "Redis cache ID"
  value       = azurerm_redis_cache.redis.id
}

output "redis_hostname" {
  description = "Redis hostname"
  value       = azurerm_redis_cache.redis.hostname
}

output "redis_port" {
  description = "Redis SSL port"
  value       = azurerm_redis_cache.redis.ssl_port
}

output "redis_primary_key" {
  description = "Redis primary access key"
  value       = azurerm_redis_cache.redis.primary_access_key
  sensitive   = true
}

output "redis_connection_string" {
  description = "Redis connection string"
  value       = "${azurerm_redis_cache.redis.hostname}:${azurerm_redis_cache.redis.ssl_port},password=${azurerm_redis_cache.redis.primary_access_key},ssl=True,abortConnect=False"
  sensitive   = true
}
