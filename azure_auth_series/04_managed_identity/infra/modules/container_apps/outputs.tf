output "environment_id" {
  value = azurerm_container_app_environment.this.id
}

output "backend_id" {
  value = azurerm_container_app.backend.id
}

output "backend_fqdn" {
  value = azurerm_container_app.backend.latest_revision_fqdn
}

output "backend_url" {
  value = "https://${azurerm_container_app.backend.ingress[0].fqdn}"
}

output "managed_identity_principal_id" {
  value = azurerm_container_app.backend.identity[0].principal_id
}

output "managed_identity_tenant_id" {
  value = azurerm_container_app.backend.identity[0].tenant_id
}
