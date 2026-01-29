terraform {
  required_version = ">= 1.5.0"

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

  # Using local backend for simplicity
  # For production, configure remote backend (Azure Storage, Terraform Cloud, etc.)
}

provider "azurerm" {
  features {}
  subscription_id = var.subscription_id
}

provider "azapi" {}

# Variables
variable "subscription_id" {
  type        = string
  description = "Azure subscription ID"
}

variable "location" {
  type        = string
  default     = "eastus2" # Required for Claude models (eastus2 or swedencentral)
  description = "Azure region for resources - must be eastus2 or swedencentral for Claude models"
}

variable "environment" {
  type        = string
  default     = "dev"
  description = "Environment name"
}

variable "project_name" {
  type        = string
  default     = "llm-router"
  description = "Project name for resource naming"
}

# Local values
locals {
  resource_prefix = "${var.project_name}-${var.environment}"
  common_tags = {
    Environment = var.environment
    Project     = var.project_name
    ManagedBy   = "Terraform"
  }
}

# Resource Group
resource "azurerm_resource_group" "main" {
  name     = "${local.resource_prefix}-rg"
  location = var.location
  tags     = local.common_tags
}

# AI Services (Microsoft Foundry - OpenAI + Claude)
module "ai_services" {
  source = "../../modules/ai_services"

  resource_group_name = azurerm_resource_group.main.name
  location            = var.location # Must be eastus2 or swedencentral
  resource_prefix     = local.resource_prefix
  tags                = local.common_tags

  depends_on = [azurerm_resource_group.main]
}

# Container Apps Environment
module "container_apps" {
  source = "../../modules/container_apps"

  resource_group_name = azurerm_resource_group.main.name
  location            = var.location
  resource_prefix     = local.resource_prefix
  tags                = local.common_tags

  depends_on = [azurerm_resource_group.main]
}

# Redis Cache
module "redis" {
  source = "../../modules/redis"

  resource_group_name = azurerm_resource_group.main.name
  location            = var.location
  resource_prefix     = local.resource_prefix
  tags                = local.common_tags

  depends_on = [azurerm_resource_group.main]
}

# Cosmos DB
module "cosmos" {
  source = "../../modules/cosmos"

  resource_group_name = azurerm_resource_group.main.name
  location            = var.location
  resource_prefix     = local.resource_prefix
  tags                = local.common_tags

  depends_on = [azurerm_resource_group.main]
}

# Monitoring
module "monitoring" {
  source = "../../modules/monitoring"

  resource_group_name = azurerm_resource_group.main.name
  location            = var.location
  resource_prefix     = local.resource_prefix
  tags                = local.common_tags

  depends_on = [azurerm_resource_group.main]
}

#######################################
# Outputs
#######################################

output "resource_group_name" {
  value = azurerm_resource_group.main.name
}

# AI Services / Foundry
output "foundry_resource_name" {
  description = "Foundry resource name (use for FOUNDRY_RESOURCE_NAME env var)"
  value       = "${local.resource_prefix}-ai"
}

output "foundry_endpoint" {
  description = "Microsoft Foundry base endpoint"
  value       = module.ai_services.foundry_endpoint
}

output "foundry_openai_endpoint" {
  description = "OpenAI-compatible endpoint for GPT models"
  value       = module.ai_services.foundry_openai_endpoint
}

output "foundry_api_key" {
  description = "Foundry API key (use for FOUNDRY_API_KEY env var)"
  value       = module.ai_services.foundry_primary_key
  sensitive   = true
}

output "model_deployments" {
  description = "All model deployment names"
  value = {
    gpt41      = module.ai_services.gpt41_deployment
    gpt41_mini = module.ai_services.gpt41_mini_deployment
    gpt41_nano = module.ai_services.gpt41_nano_deployment
  }
}

# Container Apps
output "container_apps_environment_id" {
  value = module.container_apps.environment_id
}

output "backend_url" {
  value = module.container_apps.backend_url
}

output "frontend_url" {
  value = module.container_apps.frontend_url
}

# Redis
output "redis_hostname" {
  value = module.redis.hostname
}

output "redis_connection_string" {
  value     = module.redis.connection_string
  sensitive = true
}

output "redis_url" {
  value     = module.redis.redis_url
  sensitive = true
}

# Cosmos DB
output "cosmos_endpoint" {
  value = module.cosmos.endpoint
}

output "cosmos_key" {
  value     = module.cosmos.primary_key
  sensitive = true
}

# Monitoring
output "log_analytics_workspace_id" {
  value = module.monitoring.workspace_id
}

output "app_insights_connection_string" {
  value     = module.monitoring.app_insights_connection_string
  sensitive = true
}
