variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
}

variable "location" {
  description = "Azure region for resources"
  type        = string
  default     = "eastus"
}

variable "cluster_name" {
  description = "Name of the AKS cluster"
  type        = string
}

variable "kubernetes_version" {
  description = "Kubernetes version"
  type        = string
  default     = "1.28.3"
}

variable "vm_size" {
  description = "VM size for node pool (B2s for cost optimization)"
  type        = string
  default     = "Standard_B2s"
}

variable "node_count" {
  description = "Initial number of nodes"
  type        = number
  default     = 2
}

variable "enable_auto_scaling" {
  description = "Enable auto-scaling for node pool"
  type        = bool
  default     = true
}

variable "min_node_count" {
  description = "Minimum number of nodes for auto-scaling"
  type        = number
  default     = 2
}

variable "max_node_count" {
  description = "Maximum number of nodes for auto-scaling"
  type        = number
  default     = 4
}

variable "acr_id" {
  description = "Azure Container Registry ID for role assignment"
  type        = string
  default     = ""
}

variable "attach_acr" {
  description = "Whether to attach ACR to AKS (must be true if acr_id is provided)"
  type        = bool
  default     = false
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default = {
    Environment = "development"
    Project     = "fraud-detection"
    ManagedBy   = "terraform"
  }
}
