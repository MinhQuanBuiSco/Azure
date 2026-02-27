# ── General ─────────────────────────────────────────

variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
  default     = "rg-blog4-auth"
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
    Project   = "azure-auth-series"
    Blog      = "04-managed-identity"
    ManagedBy = "Terraform"
  }
}

# ── Key Vault ──────────────────────────────────────

variable "key_vault_name" {
  description = "Name of the Key Vault (must be globally unique, 3-24 alphanumeric + hyphens)"
  type        = string
}

# ── Container Registry ─────────────────────────────

variable "acr_name" {
  description = "Name of the Container Registry (must be globally unique, alphanumeric only)"
  type        = string
}

# ── Container Apps ─────────────────────────────────

variable "container_apps_env_name" {
  description = "Name of the Container Apps Environment"
  type        = string
  default     = "cae-blog4"
}

variable "backend_app_name" {
  description = "Name of the backend container app"
  type        = string
  default     = "ca-blog4-backend"
}

variable "backend_image_name" {
  description = "Backend Docker image name (without registry prefix)"
  type        = string
  default     = "blog4-backend"
}

variable "backend_image_tag" {
  description = "Backend Docker image tag"
  type        = string
  default     = "latest"
}

variable "backend_cpu" {
  description = "CPU allocation for backend"
  type        = number
  default     = 0.25
}

variable "backend_memory" {
  description = "Memory allocation for backend"
  type        = string
  default     = "0.5Gi"
}

variable "backend_min_replicas" {
  description = "Minimum replicas (0 = scale to zero)"
  type        = number
  default     = 0
}

variable "backend_max_replicas" {
  description = "Maximum replicas"
  type        = number
  default     = 1
}

# ── Static Web App ─────────────────────────────────

variable "static_web_app_name" {
  description = "Name of the Static Web App"
  type        = string
  default     = "swa-blog4-frontend"
}

variable "static_web_app_location" {
  description = "Location for Static Web App (limited regions)"
  type        = string
  default     = "eastus2"
}
