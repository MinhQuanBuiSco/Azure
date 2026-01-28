output "id" {
  description = "AI Foundry account ID"
  value       = azurerm_cognitive_account.this.id
}

output "endpoint" {
  description = "AI Foundry endpoint"
  value       = azurerm_cognitive_account.this.endpoint
}

output "primary_access_key" {
  description = "Primary access key"
  value       = azurerm_cognitive_account.this.primary_access_key
  sensitive   = true
}

output "model_deployment_name" {
  description = "OpenAI model deployment name"
  value       = azurerm_cognitive_deployment.openai.name
}

output "model_name" {
  description = "OpenAI model name"
  value       = var.model_name
}
