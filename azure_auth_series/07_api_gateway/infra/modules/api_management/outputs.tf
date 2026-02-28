output "gateway_url" {
  description = "APIM gateway URL"
  value       = azurerm_api_management.this.gateway_url
}

output "apim_name" {
  value = azurerm_api_management.this.name
}

output "apim_id" {
  value = azurerm_api_management.this.id
}
