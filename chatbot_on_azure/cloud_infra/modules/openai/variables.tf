variable "account_name" {
  description = "Name of the Azure OpenAI account"
  type        = string
}

variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
}

variable "location" {
  description = "Azure region for OpenAI service"
  type        = string
}

variable "sku_name" {
  description = "SKU for Azure OpenAI"
  type        = string
  default     = "S0"
}

variable "deployment_name" {
  description = "Name for the model deployment"
  type        = string
}

variable "model_name" {
  description = "Name of the OpenAI model to deploy"
  type        = string
}

variable "model_version" {
  description = "Version of the OpenAI model"
  type        = string
}

variable "deployment_capacity" {
  description = "Capacity for the model deployment (in thousands of tokens per minute)"
  type        = number
  default     = 10
}

variable "tags" {
  description = "Tags to apply to the resource"
  type        = map(string)
  default     = {}
}
