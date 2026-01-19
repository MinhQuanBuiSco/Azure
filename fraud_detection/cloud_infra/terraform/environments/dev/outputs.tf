output "resource_group_name" {
  description = "Resource group name"
  value       = azurerm_resource_group.main.name
}

# AKS Outputs
output "aks_cluster_name" {
  description = "AKS cluster name"
  value       = module.aks.cluster_name
}

output "aks_cluster_id" {
  description = "AKS cluster ID"
  value       = module.aks.cluster_id
}

output "aks_fqdn" {
  description = "AKS cluster FQDN"
  value       = module.aks.cluster_fqdn
}

output "kube_config" {
  description = "Kubernetes configuration (use with caution)"
  value       = module.aks.kube_config
  sensitive   = true
}

# ACR Outputs
output "acr_login_server" {
  description = "ACR login server"
  value       = module.acr.acr_login_server
}

output "acr_name" {
  description = "ACR name"
  value       = module.acr.acr_name
}

output "acr_admin_username" {
  description = "ACR admin username"
  value       = module.acr.acr_admin_username
  sensitive   = true
}

output "acr_admin_password" {
  description = "ACR admin password"
  value       = module.acr.acr_admin_password
  sensitive   = true
}

# PostgreSQL Outputs
output "postgres_fqdn" {
  description = "PostgreSQL server FQDN"
  value       = module.databases.postgres_fqdn
}

output "postgres_admin_username" {
  description = "PostgreSQL admin username"
  value       = module.databases.postgres_admin_username
  sensitive   = true
}

output "database_name" {
  description = "Database name"
  value       = module.databases.database_name
}

# Redis Outputs
output "redis_hostname" {
  description = "Redis hostname"
  value       = module.databases.redis_hostname
}

output "redis_port" {
  description = "Redis SSL port"
  value       = module.databases.redis_port
}

output "redis_primary_key" {
  description = "Redis primary access key"
  value       = module.databases.redis_primary_key
  sensitive   = true
}

output "redis_connection_string" {
  description = "Redis connection string"
  value       = module.databases.redis_connection_string
  sensitive   = true
}
