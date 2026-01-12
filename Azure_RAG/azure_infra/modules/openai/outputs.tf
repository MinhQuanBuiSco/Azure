output "endpoint" {
  description = "OpenAI endpoint"
  value       = azurerm_cognitive_account.this.endpoint
}

output "primary_access_key" {
  description = "Primary access key"
  value       = azurerm_cognitive_account.this.primary_access_key
  sensitive   = true
}

output "secondary_access_key" {
  description = "Secondary access key"
  value       = azurerm_cognitive_account.this.secondary_access_key
  sensitive   = true
}

output "chat_deployment_name" {
  description = "Chat model deployment name"
  value       = azurerm_cognitive_deployment.chat.name
}

output "embedding_deployment_name" {
  description = "Embedding model deployment name"
  value       = azurerm_cognitive_deployment.embedding.name
}
