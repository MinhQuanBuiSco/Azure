terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
    azapi = {
      source  = "Azure/azapi"
      version = "~> 2.0"
    }
  }
}

variable "resource_group_name" {
  type        = string
  description = "Resource group name"
}

variable "location" {
  type        = string
  description = "Azure region - must be eastus2 or swedencentral for Claude models"
  default     = "eastus2"
}

variable "resource_prefix" {
  type        = string
  description = "Prefix for resource names"
}

variable "tags" {
  type        = map(string)
  description = "Resource tags"
}


#######################################
# Microsoft Foundry - Single AI Services Account
#######################################

resource "azurerm_cognitive_account" "foundry" {
  name                  = "${var.resource_prefix}-ai"
  location              = var.location
  resource_group_name   = var.resource_group_name
  kind                  = "AIServices"
  sku_name              = "S0"
  custom_subdomain_name = "${var.resource_prefix}-ai"
  tags                  = var.tags

  network_acls {
    default_action = "Allow"
  }
}

#######################################
# OpenAI Model Deployments (serialized)
#######################################

# GPT-4.1 (Frontier tier)
resource "azapi_resource" "gpt41" {
  type      = "Microsoft.CognitiveServices/accounts/deployments@2024-10-01"
  name      = "gpt-4.1"
  parent_id = azurerm_cognitive_account.foundry.id

  body = {
    sku = {
      name     = "Standard"
      capacity = 30
    }
    properties = {
      model = {
        format  = "OpenAI"
        name    = "gpt-4.1"
        version = "2025-04-14"
      }
    }
  }
}

# GPT-4.1-mini (Standard tier)
resource "azapi_resource" "gpt41_mini" {
  type      = "Microsoft.CognitiveServices/accounts/deployments@2024-10-01"
  name      = "gpt-4.1-mini"
  parent_id = azurerm_cognitive_account.foundry.id

  body = {
    sku = {
      name     = "Standard"
      capacity = 50
    }
    properties = {
      model = {
        format  = "OpenAI"
        name    = "gpt-4.1-mini"
        version = "2025-04-14"
      }
    }
  }

  depends_on = [azapi_resource.gpt41]
}

# GPT-4.1-nano (Fast tier)
resource "azapi_resource" "gpt41_nano" {
  type                      = "Microsoft.CognitiveServices/accounts/deployments@2024-10-01"
  name                      = "gpt-4.1-nano"
  parent_id                 = azurerm_cognitive_account.foundry.id
  schema_validation_enabled = false

  body = {
    sku = {
      name     = "GlobalStandard"
      capacity = 100
    }
    properties = {
      model = {
        format  = "OpenAI"
        name    = "gpt-4.1-nano"
        version = "2025-04-14"
      }
    }
  }

  depends_on = [azapi_resource.gpt41_mini]
}


#######################################
# Outputs
#######################################

output "foundry_id" {
  description = "Microsoft Foundry AI Services account ID"
  value       = azurerm_cognitive_account.foundry.id
}

output "foundry_endpoint" {
  description = "Microsoft Foundry base endpoint"
  value       = azurerm_cognitive_account.foundry.endpoint
}

output "foundry_openai_endpoint" {
  description = "OpenAI-compatible endpoint"
  value       = "${azurerm_cognitive_account.foundry.endpoint}openai"
}


output "foundry_primary_key" {
  description = "Primary API key"
  value       = azurerm_cognitive_account.foundry.primary_access_key
  sensitive   = true
}

output "gpt41_deployment" {
  value = azapi_resource.gpt41.name
}

output "gpt41_mini_deployment" {
  value = azapi_resource.gpt41_mini.name
}

output "gpt41_nano_deployment" {
  value = azapi_resource.gpt41_nano.name
}

