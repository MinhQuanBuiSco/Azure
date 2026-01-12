variable "name" {
  description = "Name of the OpenAI resource"
  type        = string
}

variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
}

variable "location" {
  description = "Azure region"
  type        = string
}

variable "sku_name" {
  description = "SKU name"
  type        = string
  default     = "S0"
}

variable "deployments" {
  description = "Model deployments configuration"
  type = object({
    chat = object({
      name     = string
      model    = string
      version  = string
      capacity = number
    })
    embedding = object({
      name     = string
      model    = string
      version  = string
      capacity = number
    })
  })
}

variable "tags" {
  description = "Tags to apply"
  type        = map(string)
  default     = {}
}
