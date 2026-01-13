output "environment_id" {
  description = "Container Apps Environment ID"
  value       = azurerm_container_app_environment.this.id
}

output "backend_id" {
  description = "Backend container app ID"
  value       = azurerm_container_app.backend.id
}

output "backend_fqdn" {
  description = "Backend container app FQDN (stable, not revision-specific)"
  value       = "${azurerm_container_app.backend.name}.${azurerm_container_app_environment.this.default_domain}"
}

output "backend_url" {
  description = "Backend container app URL (stable)"
  value       = "https://${azurerm_container_app.backend.name}.${azurerm_container_app_environment.this.default_domain}"
}
