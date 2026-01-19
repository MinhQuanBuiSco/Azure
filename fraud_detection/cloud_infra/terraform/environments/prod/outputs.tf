output "resource_group_name" {
  description = "Name of the resource group"
  value       = azurerm_resource_group.main.name
}

# AKS Outputs
output "aks_cluster_name" {
  description = "Name of the AKS cluster"
  value       = module.aks.cluster_name
}

output "aks_cluster_id" {
  description = "ID of the AKS cluster"
  value       = module.aks.cluster_id
}

output "kube_config" {
  description = "Kubernetes config for kubectl"
  value       = module.aks.kube_config
  sensitive   = true
}

# ACR Outputs
output "acr_name" {
  description = "Name of the container registry"
  value       = module.acr.acr_name
}

output "acr_login_server" {
  description = "Login server for ACR"
  value       = module.acr.login_server
}

# Database Outputs
output "postgres_fqdn" {
  description = "PostgreSQL server FQDN"
  value       = module.databases.postgres_fqdn
}

output "postgres_admin_username" {
  description = "PostgreSQL admin username"
  value       = var.postgres_admin_username
}

output "database_name" {
  description = "Database name"
  value       = module.databases.database_name
}

output "redis_hostname" {
  description = "Redis hostname"
  value       = module.databases.redis_hostname
}

output "redis_port" {
  description = "Redis SSL port"
  value       = module.databases.redis_port
}

output "redis_connection_string" {
  description = "Redis connection string"
  value       = module.databases.redis_connection_string
  sensitive   = true
}

# Key Vault
output "key_vault_name" {
  description = "Name of the Key Vault"
  value       = azurerm_key_vault.main.name
}

output "key_vault_uri" {
  description = "URI of the Key Vault"
  value       = azurerm_key_vault.main.vault_uri
}

# Monitoring
output "log_analytics_workspace_id" {
  description = "Log Analytics Workspace ID"
  value       = azurerm_log_analytics_workspace.main.id
}

output "application_insights_connection_string" {
  description = "Application Insights connection string"
  value       = azurerm_application_insights.main.connection_string
  sensitive   = true
}

output "application_insights_instrumentation_key" {
  description = "Application Insights instrumentation key"
  value       = azurerm_application_insights.main.instrumentation_key
  sensitive   = true
}
