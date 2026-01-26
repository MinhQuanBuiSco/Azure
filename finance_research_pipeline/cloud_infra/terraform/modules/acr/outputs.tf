output "login_server" {
  description = "ACR login server"
  value       = azurerm_container_registry.main.login_server
}

output "admin_username" {
  description = "ACR admin username"
  value       = azurerm_container_registry.main.admin_username
}

output "admin_password" {
  description = "ACR admin password"
  value       = azurerm_container_registry.main.admin_password
  sensitive   = true
}

output "id" {
  description = "ACR ID"
  value       = azurerm_container_registry.main.id
}

output "name" {
  description = "ACR name"
  value       = azurerm_container_registry.main.name
}
