output "openai_id" {
  description = "ID of the Azure OpenAI account"
  value       = azurerm_cognitive_account.openai.id
}

output "openai_endpoint" {
  description = "Endpoint URL for Azure OpenAI"
  value       = azurerm_cognitive_account.openai.endpoint
}

output "openai_primary_key" {
  description = "Primary access key for Azure OpenAI"
  value       = azurerm_cognitive_account.openai.primary_access_key
  sensitive   = true
}

output "openai_secondary_key" {
  description = "Secondary access key for Azure OpenAI"
  value       = azurerm_cognitive_account.openai.secondary_access_key
  sensitive   = true
}

output "deployment_name" {
  description = "Name of the model deployment"
  value       = azurerm_cognitive_deployment.model.name
}

output "deployment_id" {
  description = "ID of the model deployment"
  value       = azurerm_cognitive_deployment.model.id
}
