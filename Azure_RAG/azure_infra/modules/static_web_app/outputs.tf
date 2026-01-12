output "default_hostname" {
  description = "Default hostname"
  value       = azurerm_static_site.this.default_host_name
}

output "api_key" {
  description = "API key for deployment"
  value       = azurerm_static_site.this.api_key
  sensitive   = true
}

output "id" {
  description = "Static web app ID"
  value       = azurerm_static_site.this.id
}
