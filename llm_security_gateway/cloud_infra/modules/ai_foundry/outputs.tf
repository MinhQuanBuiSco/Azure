output "openai_id" {
  description = "Azure OpenAI resource ID"
  value       = azurerm_cognitive_account.openai.id
}

output "endpoint" {
  description = "Azure OpenAI endpoint"
  value       = azurerm_cognitive_account.openai.endpoint
}

output "primary_key" {
  description = "Azure OpenAI primary key"
  value       = azurerm_cognitive_account.openai.primary_access_key
  sensitive   = true
}

output "deployment_name" {
  description = "Primary model deployment name"
  value       = azurerm_cognitive_deployment.gpt4o.name
}

output "content_safety_endpoint" {
  description = "Azure Content Safety endpoint"
  value       = azurerm_cognitive_account.content_safety.endpoint
}

output "content_safety_key" {
  description = "Azure Content Safety primary key"
  value       = azurerm_cognitive_account.content_safety.primary_access_key
  sensitive   = true
}
