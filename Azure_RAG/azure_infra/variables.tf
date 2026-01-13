# General Variables
variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
  default     = "rg-rag-app"
}

variable "location" {
  description = "Azure region for resources"
  type        = string
  default     = "eastus2"
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default = {
    Environment = "Production"
    Application = "RAG-App"
    ManagedBy   = "Terraform"
  }
}

# Storage Account
variable "storage_account_name" {
  description = "Name of the storage account (must be globally unique)"
  type        = string
}

variable "blob_container_name" {
  description = "Name of the blob container for PDFs"
  type        = string
  default     = "pdfs"
}

# Redis Cache
variable "redis_cache_name" {
  description = "Name of the Redis cache"
  type        = string
}

variable "redis_sku" {
  description = "Redis SKU (Basic, Standard, Premium)"
  type        = string
  default     = "Standard"
}

variable "redis_capacity" {
  description = "Redis capacity (0-6 for Standard)"
  type        = number
  default     = 1  # C1
}

# Azure AI Search
variable "search_service_name" {
  description = "Name of the Azure AI Search service"
  type        = string
}

variable "search_sku" {
  description = "Azure AI Search SKU"
  type        = string
  default     = "standard"
}

variable "search_replica_count" {
  description = "Number of replicas"
  type        = number
  default     = 1
}

variable "search_partition_count" {
  description = "Number of partitions"
  type        = number
  default     = 1
}

variable "search_index_name" {
  description = "Name of the search index"
  type        = string
  default     = "rag-index"
}

# Azure OpenAI
variable "openai_name" {
  description = "Name of the Azure OpenAI resource"
  type        = string
}

variable "openai_location" {
  description = "Azure region for OpenAI (limited availability)"
  type        = string
  default     = "eastus"
}

variable "openai_sku" {
  description = "Azure OpenAI SKU"
  type        = string
  default     = "S0"
}

variable "openai_chat_deployment_name" {
  description = "Name for the chat model deployment"
  type        = string
  default     = "gpt-4o-mini"
}

variable "openai_chat_model" {
  description = "Chat model name"
  type        = string
  default     = "gpt-4o-mini"
}

variable "openai_chat_model_version" {
  description = "Chat model version"
  type        = string
  default     = "2024-07-18"
}

variable "openai_chat_capacity" {
  description = "Chat model TPM capacity (in thousands)"
  type        = number
  default     = 30
}

variable "openai_embedding_deployment_name" {
  description = "Name for the embedding model deployment"
  type        = string
  default     = "text-embedding-3-small"
}

variable "openai_embedding_model" {
  description = "Embedding model name"
  type        = string
  default     = "text-embedding-3-small"
}

variable "openai_embedding_model_version" {
  description = "Embedding model version"
  type        = string
  default     = "1"
}

variable "openai_embedding_capacity" {
  description = "Embedding model TPM capacity (in thousands)"
  type        = number
  default     = 100
}

# Container Registry
variable "acr_name" {
  description = "Name of the Azure Container Registry"
  type        = string
}

variable "acr_sku" {
  description = "ACR SKU (Basic, Standard, Premium)"
  type        = string
  default     = "Standard"
}

variable "acr_admin_enabled" {
  description = "Enable admin user for ACR"
  type        = bool
  default     = true
}

# Container Apps
variable "container_apps_env_name" {
  description = "Name of the Container Apps Environment"
  type        = string
  default     = "cae-rag-app"
}

variable "backend_app_name" {
  description = "Name of the backend container app"
  type        = string
  default     = "ca-rag-backend"
}

variable "backend_image_name" {
  description = "Backend Docker image name"
  type        = string
  default     = "rag-backend"
}

variable "backend_image_tag" {
  description = "Backend Docker image tag"
  type        = string
  default     = "latest"
}

variable "backend_cpu" {
  description = "CPU allocation for backend (0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0)"
  type        = number
  default     = 1.0
}

variable "backend_memory" {
  description = "Memory allocation for backend (0.5Gi, 1Gi, 1.5Gi, 2Gi, 3Gi, 4Gi)"
  type        = string
  default     = "2Gi"
}

variable "backend_min_replicas" {
  description = "Minimum number of backend replicas"
  type        = number
  default     = 3
}

variable "backend_max_replicas" {
  description = "Maximum number of backend replicas"
  type        = number
  default     = 50
}

# Static Web App
variable "static_web_app_name" {
  description = "Name of the static web app"
  type        = string
  default     = "swa-rag-frontend"
}

variable "static_web_app_location" {
  description = "Location for static web app"
  type        = string
  default     = "eastus2"
}

variable "static_web_app_sku" {
  description = "Static Web App SKU (Free or Standard)"
  type        = string
  default     = "Standard"
}

# Application Insights
variable "app_insights_name" {
  description = "Name of Application Insights"
  type        = string
  default     = "appi-rag-app"
}
