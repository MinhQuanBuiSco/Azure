output "account_name" {
  description = "Storage account name"
  value       = azurerm_storage_account.this.name
}

output "primary_access_key" {
  description = "Primary access key"
  value       = azurerm_storage_account.this.primary_access_key
  sensitive   = true
}

output "connection_string" {
  description = "Primary connection string"
  value       = azurerm_storage_account.this.primary_connection_string
  sensitive   = true
}

output "container_name" {
  description = "Blob container name"
  value       = azurerm_storage_container.this.name
}

output "primary_blob_endpoint" {
  description = "Primary blob endpoint"
  value       = azurerm_storage_account.this.primary_blob_endpoint
}
