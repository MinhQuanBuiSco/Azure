variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
}

variable "location" {
  description = "Azure region"
  type        = string
}

variable "resource_group_name" {
  description = "Resource group name"
  type        = string
}

variable "log_analytics_workspace_id" {
  description = "Log Analytics workspace ID"
  type        = string
}

variable "acr_login_server" {
  description = "ACR login server"
  type        = string
}

variable "acr_admin_username" {
  description = "ACR admin username"
  type        = string
}

variable "acr_admin_password" {
  description = "ACR admin password"
  type        = string
  sensitive   = true
}

variable "backend_image_name" {
  description = "Backend Docker image name"
  type        = string
  default     = "finance-research-backend"
}

variable "backend_image_tag" {
  description = "Backend Docker image tag"
  type        = string
  default     = "latest"
}

variable "frontend_image_name" {
  description = "Frontend Docker image name"
  type        = string
  default     = "finance-research-frontend"
}

variable "frontend_image_tag" {
  description = "Frontend Docker image tag"
  type        = string
  default     = "latest"
}

variable "backend_cpu" {
  description = "Backend CPU allocation"
  type        = number
  default     = 1.0
}

variable "backend_memory" {
  description = "Backend memory allocation"
  type        = string
  default     = "2Gi"
}

variable "frontend_cpu" {
  description = "Frontend CPU allocation"
  type        = number
  default     = 0.5
}

variable "frontend_memory" {
  description = "Frontend memory allocation"
  type        = string
  default     = "1Gi"
}

variable "backend_min_replicas" {
  description = "Backend minimum replicas"
  type        = number
  default     = 1
}

variable "backend_max_replicas" {
  description = "Backend maximum replicas"
  type        = number
  default     = 3
}

variable "frontend_min_replicas" {
  description = "Frontend minimum replicas"
  type        = number
  default     = 1
}

variable "frontend_max_replicas" {
  description = "Frontend maximum replicas"
  type        = number
  default     = 3
}

variable "azure_openai_endpoint" {
  description = "Azure OpenAI endpoint"
  type        = string
  sensitive   = true
}

variable "azure_openai_api_key" {
  description = "Azure OpenAI API key"
  type        = string
  sensitive   = true
}

variable "azure_openai_deployment_name" {
  description = "Azure OpenAI deployment name"
  type        = string
  default     = "gpt-4o"
}

variable "tavily_api_key" {
  description = "Tavily API key"
  type        = string
  sensitive   = true
}

variable "newsapi_key" {
  description = "NewsAPI key"
  type        = string
  sensitive   = true
}

variable "redis_host" {
  description = "Redis host"
  type        = string
}

variable "redis_password" {
  description = "Redis password"
  type        = string
  sensitive   = true
}

variable "cosmos_endpoint" {
  description = "Cosmos DB endpoint"
  type        = string
}

variable "cosmos_key" {
  description = "Cosmos DB key"
  type        = string
  sensitive   = true
}

variable "cors_origins" {
  description = "CORS allowed origins"
  type        = list(string)
  default     = []
}

variable "tags" {
  description = "Resource tags"
  type        = map(string)
  default     = {}
}
