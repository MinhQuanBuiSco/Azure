output "environment_id" {
  description = "Container App Environment ID"
  value       = azurerm_container_app_environment.main.id
}

output "backend_fqdn" {
  description = "Backend Container App FQDN"
  value       = azurerm_container_app.backend.ingress[0].fqdn
}

output "backend_url" {
  description = "Backend Container App URL"
  value       = "https://${azurerm_container_app.backend.ingress[0].fqdn}"
}

output "frontend_fqdn" {
  description = "Frontend Container App FQDN"
  value       = azurerm_container_app.frontend.ingress[0].fqdn
}

output "frontend_url" {
  description = "Frontend Container App URL"
  value       = "https://${azurerm_container_app.frontend.ingress[0].fqdn}"
}

output "backend_name" {
  description = "Backend Container App name"
  value       = azurerm_container_app.backend.name
}

output "frontend_name" {
  description = "Frontend Container App name"
  value       = azurerm_container_app.frontend.name
}
