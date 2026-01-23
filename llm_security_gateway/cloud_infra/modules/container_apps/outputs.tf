output "environment_id" {
  description = "Container Apps Environment ID"
  value       = azurerm_container_app_environment.main.id
}

output "backend_id" {
  description = "Backend Container App ID"
  value       = azurerm_container_app.backend.id
}

output "backend_url" {
  description = "Backend Container App URL"
  value       = "https://${azurerm_container_app.backend.ingress[0].fqdn}"
}

output "frontend_id" {
  description = "Frontend Container App ID"
  value       = azurerm_container_app.frontend.id
}

output "frontend_url" {
  description = "Frontend Container App URL"
  value       = "https://${azurerm_container_app.frontend.ingress[0].fqdn}"
}
