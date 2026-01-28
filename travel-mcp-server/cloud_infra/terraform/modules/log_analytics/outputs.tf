output "id" {
  description = "Log Analytics workspace ID"
  value       = azurerm_log_analytics_workspace.this.id
}

output "workspace_id" {
  description = "Log Analytics workspace GUID"
  value       = azurerm_log_analytics_workspace.this.workspace_id
}

output "primary_shared_key" {
  description = "Primary shared key"
  value       = azurerm_log_analytics_workspace.this.primary_shared_key
  sensitive   = true
}
