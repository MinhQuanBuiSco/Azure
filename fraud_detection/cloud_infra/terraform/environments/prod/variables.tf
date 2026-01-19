variable "location" {
  description = "Azure region for resources"
  type        = string
  default     = "eastus"
}

variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
  default     = "fraud-detection-prod-rg"
}

variable "project_prefix" {
  description = "Prefix for resource names"
  type        = string
  default     = "frauddet"
}

variable "aks_cluster_name" {
  description = "Name of the AKS cluster"
  type        = string
  default     = "fraud-detection-aks-prod"
}

variable "kubernetes_version" {
  description = "Kubernetes version for AKS"
  type        = string
  default     = "1.28"
}

variable "acr_name" {
  description = "Name of Azure Container Registry (must be globally unique, alphanumeric only)"
  type        = string
}

variable "postgres_name" {
  description = "Name of PostgreSQL server"
  type        = string
  default     = "fraud-detection-postgres-prod"
}

variable "postgres_admin_username" {
  description = "PostgreSQL admin username"
  type        = string
  default     = "fraudadmin"
}

variable "postgres_admin_password" {
  description = "PostgreSQL admin password"
  type        = string
  sensitive   = true
}

variable "redis_name" {
  description = "Name of Redis cache"
  type        = string
  default     = "fraud-detection-redis-prod"
}

variable "enable_private_endpoints" {
  description = "Enable private endpoints for databases"
  type        = bool
  default     = true
}

variable "private_endpoint_subnet_id" {
  description = "Subnet ID for private endpoints"
  type        = string
  default     = ""
}

variable "allowed_ip_ranges" {
  description = "List of IP ranges allowed to access Key Vault"
  type        = list(string)
  default     = []
}

variable "azure_ai_endpoint" {
  description = "Azure AI Foundry endpoint for Claude"
  type        = string
  default     = ""
}

variable "azure_ai_key" {
  description = "Azure AI Foundry API key"
  type        = string
  sensitive   = true
  default     = ""
}

variable "azure_ai_model_name" {
  description = "Azure AI model name (e.g., claude-3-5-sonnet)"
  type        = string
  default     = "claude-3-5-sonnet"
}

variable "azure_anomaly_endpoint" {
  description = "Azure Anomaly Detector endpoint"
  type        = string
  default     = ""
}

variable "azure_anomaly_key" {
  description = "Azure Anomaly Detector API key"
  type        = string
  sensitive   = true
  default     = ""
}
