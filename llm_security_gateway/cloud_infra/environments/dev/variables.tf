variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}

variable "location" {
  description = "Azure region for resources"
  type        = string
  default     = "eastus"
}

variable "ai_location" {
  description = "Azure region for AI services (may differ from main region)"
  type        = string
  default     = "eastus"
}

variable "backend_image" {
  description = "Backend container image"
  type        = string
  # Using Azure's sample image as placeholder - replace with your ACR image
  default     = "mcr.microsoft.com/azuredocs/containerapps-helloworld:latest"
}

variable "frontend_image" {
  description = "Frontend container image"
  type        = string
  # Using Azure's sample image as placeholder - replace with your ACR image
  default     = "mcr.microsoft.com/azuredocs/containerapps-helloworld:latest"
}
