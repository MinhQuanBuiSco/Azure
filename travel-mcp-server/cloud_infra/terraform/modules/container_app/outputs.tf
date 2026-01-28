output "id" {
  description = "Container App ID"
  value       = azurerm_container_app.this.id
}

output "name" {
  description = "Container App name"
  value       = azurerm_container_app.this.name
}

output "fqdn" {
  description = "Container App FQDN"
  value       = var.ingress_enabled ? azurerm_container_app.this.ingress[0].fqdn : null
}

output "url" {
  description = "Container App URL"
  value       = var.ingress_enabled ? "https://${azurerm_container_app.this.ingress[0].fqdn}" : null
}

output "latest_revision_name" {
  description = "Latest revision name"
  value       = azurerm_container_app.this.latest_revision_name
}
