output "name" {
  description = "Search service name"
  value       = azurerm_search_service.this.name
}

output "endpoint" {
  description = "Search service endpoint"
  value       = "https://${azurerm_search_service.this.name}.search.windows.net"
}

output "primary_admin_key" {
  description = "Primary admin key"
  value       = azurerm_search_service.this.primary_key
  sensitive   = true
}

output "secondary_admin_key" {
  description = "Secondary admin key"
  value       = azurerm_search_service.this.secondary_key
  sensitive   = true
}
