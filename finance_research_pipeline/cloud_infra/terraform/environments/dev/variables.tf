variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "finresearch"
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "location" {
  description = "Azure region"
  type        = string
  default     = "eastus"
}

variable "backend_image_tag" {
  description = "Backend Docker image tag"
  type        = string
  default     = "latest"
}

variable "frontend_image_tag" {
  description = "Frontend Docker image tag"
  type        = string
  default     = "latest"
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

variable "tags" {
  description = "Additional resource tags"
  type        = map(string)
  default     = {}
}
