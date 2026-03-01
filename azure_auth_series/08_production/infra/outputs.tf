output "resource_group_name" {
  value = module.resource_group.name
}

output "acr_login_server" {
  value = module.container_registry.login_server
}

output "acr_name" {
  value = module.container_registry.name
}

output "task_api_url" {
  value = module.container_apps.task_api_url
}

output "notification_url" {
  value = module.container_apps.notification_url
}

output "audit_url" {
  value = module.container_apps.audit_url
}

output "frontend_url" {
  description = "Frontend Container App URL"
  value       = module.container_apps.frontend_url
}

output "apim_gateway_url" {
  description = "API Management gateway URL — use this in frontend"
  value       = module.api_management.gateway_url
}

output "apim_name" {
  value = module.api_management.apim_name
}

# ── Monitoring ─────────────────────────────────────────

output "app_insights_name" {
  description = "Application Insights resource name"
  value       = module.monitoring.app_insights_name
}

output "app_insights_connection_string" {
  description = "Application Insights connection string"
  value       = module.monitoring.connection_string
  sensitive   = true
}
