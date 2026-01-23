output "resource_group_name" {
  description = "Resource group name"
  value       = azurerm_resource_group.main.name
}

output "backend_url" {
  description = "Backend API URL"
  value       = module.container_apps.backend_url
}

output "frontend_url" {
  description = "Frontend URL"
  value       = module.container_apps.frontend_url
}

# Azure AI / OpenAI outputs
output "azure_ai_endpoint" {
  description = "Azure OpenAI endpoint (AZURE_AI_ENDPOINT)"
  value       = module.ai_foundry.endpoint
}

output "azure_ai_api_key" {
  description = "Azure OpenAI API key (AZURE_AI_API_KEY)"
  value       = module.ai_foundry.primary_key
  sensitive   = true
}

output "azure_ai_deployment_name" {
  description = "Azure OpenAI deployment name (AZURE_AI_DEPLOYMENT_NAME)"
  value       = module.ai_foundry.deployment_name
}

# Azure Content Safety outputs
output "azure_content_safety_endpoint" {
  description = "Azure Content Safety endpoint (AZURE_CONTENT_SAFETY_ENDPOINT)"
  value       = module.ai_foundry.content_safety_endpoint
}

output "azure_content_safety_key" {
  description = "Azure Content Safety key (AZURE_CONTENT_SAFETY_KEY)"
  value       = module.ai_foundry.content_safety_key
  sensitive   = true
}

output "key_vault_name" {
  description = "Key Vault name"
  value       = module.key_vault.key_vault_name
}

output "cosmos_endpoint" {
  description = "Cosmos DB endpoint"
  value       = module.cosmos.endpoint
}

output "cosmos_connection_string" {
  description = "Cosmos DB connection string (COSMOS_CONNECTION_STRING)"
  value       = module.cosmos.connection_string
  sensitive   = true
}

output "redis_hostname" {
  description = "Redis hostname"
  value       = module.redis.hostname
}

output "redis_connection_string" {
  description = "Redis connection string (REDIS_URL)"
  value       = module.redis.connection_string
  sensitive   = true
}

# Container Registry outputs
output "acr_login_server" {
  description = "ACR login server URL"
  value       = module.acr.login_server
}

output "acr_name" {
  description = "ACR name"
  value       = module.acr.name
}

output "acr_admin_username" {
  description = "ACR admin username"
  value       = module.acr.admin_username
}

output "acr_admin_password" {
  description = "ACR admin password"
  value       = module.acr.admin_password
  sensitive   = true
}
