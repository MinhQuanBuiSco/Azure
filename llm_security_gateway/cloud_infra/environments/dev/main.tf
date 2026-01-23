terraform {
  required_version = ">= 1.5.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.85"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }

  # Uncomment for remote state
  # backend "azurerm" {
  #   resource_group_name  = "tfstate-rg"
  #   storage_account_name = "tfstateXXXXX"
  #   container_name       = "tfstate"
  #   key                  = "llm-gateway-dev.tfstate"
  # }
}

provider "azurerm" {
  features {
    resource_group {
      prevent_deletion_if_contains_resources = false
    }
    key_vault {
      purge_soft_delete_on_destroy    = true
      recover_soft_deleted_key_vaults = true
    }
  }
}

# Random suffix for unique naming
resource "random_string" "suffix" {
  length  = 6
  special = false
  upper   = false
}

locals {
  name_suffix = random_string.suffix.result
  common_tags = {
    Environment = var.environment
    Project     = "llm-security-gateway"
    ManagedBy   = "terraform"
  }
}

# Resource Group
resource "azurerm_resource_group" "main" {
  name     = "rg-llm-gateway-${var.environment}-${local.name_suffix}"
  location = var.location
  tags     = local.common_tags
}

# Monitoring Module
module "monitoring" {
  source = "../../modules/monitoring"

  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  environment         = var.environment
  name_suffix         = local.name_suffix
  tags                = local.common_tags
}

# Key Vault Module
module "key_vault" {
  source = "../../modules/key_vault"

  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  environment         = var.environment
  name_suffix         = local.name_suffix
  tags                = local.common_tags
}

# Redis Cache Module
module "redis" {
  source = "../../modules/redis_cache"

  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  environment         = var.environment
  name_suffix         = local.name_suffix
  tags                = local.common_tags
  sku_name            = "Basic"
  family              = "C"
  capacity            = 0
}

# Cosmos DB Module
module "cosmos" {
  source = "../../modules/cosmos_db"

  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  environment         = var.environment
  name_suffix         = local.name_suffix
  tags                = local.common_tags
}

# Container Registry Module
module "acr" {
  source = "../../modules/container_registry"

  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  environment         = var.environment
  name_suffix         = local.name_suffix
  tags                = local.common_tags
}

# AI Foundry Module
module "ai_foundry" {
  source = "../../modules/ai_foundry"

  resource_group_name            = azurerm_resource_group.main.name
  location                       = var.ai_location
  environment                    = var.environment
  name_suffix                    = local.name_suffix
  tags                           = local.common_tags
  log_analytics_workspace_id     = module.monitoring.log_analytics_workspace_id
  application_insights_id        = module.monitoring.application_insights_id
  application_insights_connection_string = module.monitoring.application_insights_connection_string
  enable_diagnostics             = true

  depends_on = [module.monitoring]
}

# Container Apps Module
module "container_apps" {
  source = "../../modules/container_apps"

  resource_group_name            = azurerm_resource_group.main.name
  location                       = azurerm_resource_group.main.location
  environment                    = var.environment
  name_suffix                    = local.name_suffix
  tags                           = local.common_tags
  log_analytics_workspace_id     = module.monitoring.log_analytics_workspace_id

  # Container configuration - use ACR images
  backend_image  = "${module.acr.login_server}/backend:latest"
  frontend_image = "${module.acr.login_server}/frontend:latest"

  # ACR credentials
  registry_server   = module.acr.login_server
  registry_username = module.acr.admin_username
  registry_password = module.acr.admin_password

  # Environment variables
  azure_ai_endpoint              = module.ai_foundry.endpoint
  azure_ai_api_key               = module.ai_foundry.primary_key
  azure_ai_deployment_name       = module.ai_foundry.deployment_name
  azure_content_safety_endpoint  = module.ai_foundry.content_safety_endpoint
  azure_content_safety_key       = module.ai_foundry.content_safety_key
  redis_connection_string        = module.redis.connection_string
  cosmos_connection_string       = module.cosmos.connection_string
  application_insights_connection_string = module.monitoring.application_insights_connection_string

  # Secrets from Key Vault
  key_vault_id = module.key_vault.key_vault_id

  depends_on = [
    module.redis,
    module.cosmos,
    module.ai_foundry,
    module.monitoring,
    module.acr
  ]
}
