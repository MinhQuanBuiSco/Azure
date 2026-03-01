output "instrumentation_key" {
  description = "Application Insights instrumentation key"
  value       = azurerm_application_insights.this.instrumentation_key
  sensitive   = true
}

output "connection_string" {
  description = "Application Insights connection string"
  value       = azurerm_application_insights.this.connection_string
  sensitive   = true
}

output "app_insights_id" {
  description = "Application Insights resource ID"
  value       = azurerm_application_insights.this.id
}

output "app_insights_name" {
  description = "Application Insights resource name"
  value       = azurerm_application_insights.this.name
}

output "log_analytics_workspace_id" {
  description = "Log Analytics workspace ID (shared with Container Apps)"
  value       = azurerm_log_analytics_workspace.this.id
}
