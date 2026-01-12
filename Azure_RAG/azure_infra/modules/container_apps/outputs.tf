output "environment_id" {
  description = "Container Apps Environment ID"
  value       = azurerm_container_app_environment.this.id
}

output "backend_id" {
  description = "Backend container app ID"
  value       = azurerm_container_app.backend.id
}

output "backend_fqdn" {
  description = "Backend container app FQDN"
  value       = azurerm_container_app.backend.latest_revision_fqdn
}

output "backend_url" {
  description = "Backend container app URL"
  value       = "https://${azurerm_container_app.backend.latest_revision_fqdn}"
}
