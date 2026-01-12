# Resource Group
output "resource_group_name" {
  description = "Name of the resource group"
  value       = module.resource_group.name
}

output "resource_group_location" {
  description = "Location of the resource group"
  value       = module.resource_group.location
}

# Storage
output "storage_account_name" {
  description = "Name of the storage account"
  value       = module.storage.account_name
}

output "storage_connection_string" {
  description = "Storage account connection string"
  value       = module.storage.connection_string
  sensitive   = true
}

output "blob_container_name" {
  description = "Name of the blob container"
  value       = module.storage.container_name
}

# Redis
output "redis_hostname" {
  description = "Redis cache hostname"
  value       = module.redis.hostname
}

output "redis_port" {
  description = "Redis cache SSL port"
  value       = module.redis.ssl_port
}

output "redis_primary_key" {
  description = "Redis primary access key"
  value       = module.redis.primary_access_key
  sensitive   = true
}

# AI Search
output "search_endpoint" {
  description = "Azure AI Search endpoint"
  value       = module.ai_search.endpoint
}

output "search_primary_key" {
  description = "Azure AI Search primary admin key"
  value       = module.ai_search.primary_admin_key
  sensitive   = true
}

output "search_index_name" {
  description = "Name of the search index"
  value       = var.search_index_name
}

# OpenAI
output "openai_endpoint" {
  description = "Azure OpenAI endpoint"
  value       = module.openai.endpoint
}

output "openai_primary_key" {
  description = "Azure OpenAI primary key"
  value       = module.openai.primary_access_key
  sensitive   = true
}

output "openai_chat_deployment" {
  description = "Name of the chat model deployment"
  value       = var.openai_chat_deployment_name
}

output "openai_embedding_deployment" {
  description = "Name of the embedding model deployment"
  value       = var.openai_embedding_deployment_name
}

# Container Registry
output "acr_login_server" {
  description = "ACR login server"
  value       = module.container_registry.login_server
}

output "acr_admin_username" {
  description = "ACR admin username"
  value       = module.container_registry.admin_username
}

output "acr_admin_password" {
  description = "ACR admin password"
  value       = module.container_registry.admin_password
  sensitive   = true
}

# Container Apps
output "backend_url" {
  description = "Backend container app URL"
  value       = "https://${module.container_apps_env.backend_fqdn}"
}

output "backend_fqdn" {
  description = "Backend container app FQDN"
  value       = module.container_apps_env.backend_fqdn
}

# Static Web App
output "frontend_url" {
  description = "Frontend static web app URL"
  value       = module.static_web_app.default_hostname
}

output "frontend_deployment_token" {
  description = "Static web app deployment token"
  value       = module.static_web_app.api_key
  sensitive   = true
}

# Application Insights
output "app_insights_instrumentation_key" {
  description = "Application Insights instrumentation key"
  value       = module.app_insights.instrumentation_key
  sensitive   = true
}

output "app_insights_connection_string" {
  description = "Application Insights connection string"
  value       = module.app_insights.connection_string
  sensitive   = true
}

# Environment Configuration (for .env files)
output "backend_env_config" {
  description = "Backend environment configuration"
  value = {
    AZURE_STORAGE_ACCOUNT_NAME            = module.storage.account_name
    AZURE_STORAGE_CONTAINER_NAME          = var.blob_container_name
    AZURE_SEARCH_ENDPOINT                 = module.ai_search.endpoint
    AZURE_SEARCH_INDEX_NAME               = var.search_index_name
    AZURE_OPENAI_ENDPOINT                 = module.openai.endpoint
    AZURE_OPENAI_CHAT_DEPLOYMENT          = var.openai_chat_deployment_name
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT     = var.openai_embedding_deployment_name
    REDIS_HOST                            = module.redis.hostname
    REDIS_PORT                            = "6380"
    REDIS_SSL                             = "true"
    APPLICATIONINSIGHTS_CONNECTION_STRING = module.app_insights.connection_string
  }
  sensitive = true
}

output "backend_secrets" {
  description = "Backend secrets (use securely)"
  value = {
    AZURE_STORAGE_CONNECTION_STRING = module.storage.connection_string
    AZURE_SEARCH_API_KEY            = module.ai_search.primary_admin_key
    AZURE_OPENAI_API_KEY            = module.openai.primary_access_key
    REDIS_PASSWORD                  = module.redis.primary_access_key
  }
  sensitive = true
}
