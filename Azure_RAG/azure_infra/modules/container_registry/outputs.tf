output "login_server" {
  description = "Container registry login server"
  value       = azurerm_container_registry.this.login_server
}

output "admin_username" {
  description = "Admin username"
  value       = azurerm_container_registry.this.admin_username
}

output "admin_password" {
  description = "Admin password"
  value       = azurerm_container_registry.this.admin_password
  sensitive   = true
}

output "id" {
  description = "Container registry ID"
  value       = azurerm_container_registry.this.id
}
