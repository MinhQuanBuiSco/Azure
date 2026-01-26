output "resource_group_name" {
  description = "Resource group name"
  value       = azurerm_resource_group.main.name
}

output "acr_login_server" {
  description = "ACR login server"
  value       = module.acr.login_server
}

output "acr_name" {
  description = "ACR name"
  value       = module.acr.name
}

output "redis_hostname" {
  description = "Redis hostname"
  value       = module.redis.hostname
}

output "cosmos_endpoint" {
  description = "Cosmos DB endpoint"
  value       = module.cosmos_db.endpoint
}

output "backend_url" {
  description = "Backend application URL"
  value       = module.container_apps.backend_url
}

output "frontend_url" {
  description = "Frontend application URL"
  value       = module.container_apps.frontend_url
}

output "log_analytics_workspace_id" {
  description = "Log Analytics workspace ID"
  value       = module.monitoring.log_analytics_workspace_id
}

output "application_insights_instrumentation_key" {
  description = "Application Insights instrumentation key"
  value       = module.monitoring.application_insights_instrumentation_key
  sensitive   = true
}
