variable "location" {
  description = "Azure region for resources"
  type        = string
  default     = "eastus2"  # eastus has PostgreSQL restrictions
}

variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
  default     = "fraud-detection-dev-rg"
}

# AKS Variables
variable "aks_cluster_name" {
  description = "Name of the AKS cluster"
  type        = string
  default     = "fraud-detection-aks-dev"
}

variable "kubernetes_version" {
  description = "Kubernetes version"
  type        = string
  default     = "1.32.0"
}

variable "vm_size" {
  description = "VM size for AKS nodes"
  type        = string
  default     = "Standard_B2s_v2"  # B2s not available, use v2
}

# ACR Variables
variable "acr_name" {
  description = "Name of ACR (must be globally unique, alphanumeric only)"
  type        = string
  default     = "frauddetectionacr"
}

# PostgreSQL Variables
variable "postgres_name" {
  description = "Name of PostgreSQL server"
  type        = string
  default     = "fraud-detection-postgres-dev"
}

variable "postgres_admin_username" {
  description = "PostgreSQL admin username"
  type        = string
  default     = "pgadmin"
}

variable "postgres_admin_password" {
  description = "PostgreSQL admin password"
  type        = string
  sensitive   = true
}

# Redis Variables
variable "redis_name" {
  description = "Name of Redis cache"
  type        = string
  default     = "fraud-detection-redis-dev"
}
