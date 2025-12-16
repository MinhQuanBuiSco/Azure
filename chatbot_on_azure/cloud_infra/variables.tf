variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "chatbot"
}

variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
  default     = "rg-chatbot-dev"
}

variable "location" {
  description = "Azure region for resources"
  type        = string
  default     = "eastus"
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default = {
    Environment = "Development"
    Project     = "Chatbot"
    ManagedBy   = "Terraform"
  }
}

# Network variables
variable "vnet_address_space" {
  description = "Address space for the virtual network"
  type        = list(string)
  default     = ["10.0.0.0/16"]
}

variable "aks_subnet_prefix" {
  description = "Address prefix for AKS subnet"
  type        = list(string)
  default     = ["10.0.1.0/24"]
}

# ACR variables
variable "acr_name" {
  description = "Name of the Azure Container Registry (must be globally unique, alphanumeric only)"
  type        = string
  default     = "acrchatbot"

  validation {
    condition     = can(regex("^[a-zA-Z0-9]*$", var.acr_name))
    error_message = "ACR name must contain only alphanumeric characters."
  }
}

variable "acr_sku" {
  description = "SKU for Azure Container Registry"
  type        = string
  default     = "Basic"

  validation {
    condition     = contains(["Basic", "Standard", "Premium"], var.acr_sku)
    error_message = "ACR SKU must be Basic, Standard, or Premium."
  }
}

# AKS variables
variable "aks_cluster_name" {
  description = "Name of the AKS cluster"
  type        = string
  default     = "aks-chatbot"
}

variable "aks_dns_prefix" {
  description = "DNS prefix for the AKS cluster"
  type        = string
  default     = "chatbot"
}

variable "kubernetes_version" {
  description = "Kubernetes version for AKS"
  type        = string
  default     = "1.33"
}

variable "aks_node_count" {
  description = "Number of nodes in the AKS cluster"
  type        = number
  default     = 2
}

variable "aks_vm_size" {
  description = "VM size for AKS nodes"
  type        = string
  default     = "Standard_B2s"
}

# Azure OpenAI variables
variable "openai_account_name" {
  description = "Name of the Azure OpenAI account"
  type        = string
  default     = "openai-chatbot"
}

variable "openai_location" {
  description = "Azure region for OpenAI (limited availability)"
  type        = string
  default     = "japaneast"

  validation {
    condition     = contains(["eastus", "southcentralus", "westeurope", "francecentral", "uksouth", "swedencentral", "japaneast"], var.openai_location)
    error_message = "Azure OpenAI is only available in specific regions. Check https://aka.ms/oai/regions for current list."
  }
}

variable "openai_sku" {
  description = "SKU for Azure OpenAI"
  type        = string
  default     = "S0"
}

variable "openai_deployment_name" {
  description = "Name for the model deployment"
  type        = string
  default     = "gpt-4"
}

variable "openai_model_name" {
  description = "Name of the OpenAI model to deploy"
  type        = string
  default     = "gpt-4"

  validation {
    condition     = contains(["gpt-35-turbo", "gpt-4", "gpt-4-32k"], var.openai_model_name)
    error_message = "Model must be one of: gpt-35-turbo, gpt-4, gpt-4-32k."
  }
}

variable "openai_model_version" {
  description = "Version of the OpenAI model"
  type        = string
  default     = "turbo-2024-04-09"
}

variable "openai_deployment_capacity" {
  description = "Capacity for the model deployment (in thousands of tokens per minute)"
  type        = number
  default     = 10
}
