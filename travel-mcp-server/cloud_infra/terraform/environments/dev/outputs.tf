output "resource_group_name" {
  description = "Name of the resource group"
  value       = module.resource_group.name
}

output "acr_login_server" {
  description = "Azure Container Registry login server"
  value       = module.acr.login_server
}

output "acr_admin_username" {
  description = "ACR admin username"
  value       = module.acr.admin_username
  sensitive   = true
}

output "backend_url" {
  description = "Backend Container App URL"
  value       = module.backend.url
}

output "frontend_url" {
  description = "Frontend Container App URL"
  value       = module.frontend.url
}

output "redis_hostname" {
  description = "Redis Cache hostname"
  value       = module.redis.hostname
}

output "log_analytics_workspace_id" {
  description = "Log Analytics Workspace ID"
  value       = module.log_analytics.workspace_id
}

output "ai_foundry_endpoint" {
  description = "Azure OpenAI endpoint"
  value       = module.ai_foundry.endpoint
}

output "ai_foundry_model" {
  description = "Deployed OpenAI model name"
  value       = module.ai_foundry.model_deployment_name
}
