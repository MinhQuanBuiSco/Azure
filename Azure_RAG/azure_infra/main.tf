terraform {
  required_version = ">= 1.5.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.116.0"
    }
    azapi = {
      source  = "azure/azapi"
      version = "~> 1.13.0"
    }
  }

  # Backend configuration for state storage
  # Uncomment and configure for production
  # backend "azurerm" {
  #   resource_group_name  = "terraform-state-rg"
  #   storage_account_name = "tfstatexxxxx"
  #   container_name       = "tfstate"
  #   key                  = "rag-app.terraform.tfstate"
  # }
}

provider "azurerm" {
  features {
    resource_group {
      prevent_deletion_if_contains_resources = false
    }
    key_vault {
      purge_soft_delete_on_destroy = true
    }
  }
}

provider "azapi" {}

# Data source for current Azure client config
data "azurerm_client_config" "current" {}

# Resource Group
module "resource_group" {
  source = "./modules/resource_group"

  name     = var.resource_group_name
  location = var.location
  tags     = var.tags
}

# Storage Account (Blob Storage for PDFs)
module "storage" {
  source = "./modules/storage"

  name                = var.storage_account_name
  resource_group_name = module.resource_group.name
  location            = var.location
  container_name      = var.blob_container_name
  tags                = var.tags
}

# Redis Cache
module "redis" {
  source = "./modules/redis"

  name                = var.redis_cache_name
  resource_group_name = module.resource_group.name
  location            = var.location
  sku_name            = var.redis_sku
  capacity            = var.redis_capacity
  tags                = var.tags
}

# Azure AI Search
module "ai_search" {
  source = "./modules/ai_search"

  name                = var.search_service_name
  resource_group_name = module.resource_group.name
  location            = var.location
  sku                 = var.search_sku
  replica_count       = var.search_replica_count
  partition_count     = var.search_partition_count
  tags                = var.tags
}

# Azure OpenAI
module "openai" {
  source = "./modules/openai"

  name                = var.openai_name
  resource_group_name = module.resource_group.name
  location            = var.openai_location
  sku_name            = var.openai_sku

  deployments = {
    chat = {
      name  = var.openai_chat_deployment_name
      model = var.openai_chat_model
      version = var.openai_chat_model_version
      capacity = var.openai_chat_capacity
    }
    embedding = {
      name  = var.openai_embedding_deployment_name
      model = var.openai_embedding_model
      version = var.openai_embedding_model_version
      capacity = var.openai_embedding_capacity
    }
  }

  tags = var.tags
}

# Container Registry
module "container_registry" {
  source = "./modules/container_registry"

  name                = var.acr_name
  resource_group_name = module.resource_group.name
  location            = var.location
  sku                 = var.acr_sku
  admin_enabled       = var.acr_admin_enabled
  tags                = var.tags
}

# Application Insights
module "app_insights" {
  source = "./modules/app_insights"

  name                = var.app_insights_name
  resource_group_name = module.resource_group.name
  location            = var.location
  application_type    = "web"
  tags                = var.tags
}

# Container Apps Environment
module "container_apps_env" {
  source = "./modules/container_apps"

  environment_name         = var.container_apps_env_name
  resource_group_name      = module.resource_group.name
  location                 = var.location
  log_analytics_workspace_id = module.app_insights.workspace_id

  # Backend Container App
  backend_app_name = var.backend_app_name
  backend_image    = "${module.container_registry.login_server}/${var.backend_image_name}:${var.backend_image_tag}"
  backend_cpu      = var.backend_cpu
  backend_memory   = var.backend_memory
  backend_min_replicas = var.backend_min_replicas
  backend_max_replicas = var.backend_max_replicas

  backend_env_vars = [
    {
      name  = "AZURE_STORAGE_ACCOUNT_NAME"
      value = module.storage.account_name
    },
    {
      name  = "AZURE_STORAGE_CONTAINER_NAME"
      value = var.blob_container_name
    },
    {
      name  = "AZURE_SEARCH_ENDPOINT"
      value = module.ai_search.endpoint
    },
    {
      name  = "AZURE_SEARCH_INDEX_NAME"
      value = var.search_index_name
    },
    {
      name  = "AZURE_OPENAI_ENDPOINT"
      value = module.openai.endpoint
    },
    {
      name  = "AZURE_OPENAI_CHAT_DEPLOYMENT"
      value = var.openai_chat_deployment_name
    },
    {
      name  = "AZURE_OPENAI_EMBEDDING_DEPLOYMENT"
      value = var.openai_embedding_deployment_name
    },
    {
      name  = "REDIS_HOST"
      value = module.redis.hostname
    },
    {
      name  = "REDIS_PORT"
      value = "6380"
    },
    {
      name  = "REDIS_SSL"
      value = "true"
    },
    {
      name  = "APPLICATIONINSIGHTS_CONNECTION_STRING"
      value = module.app_insights.connection_string
    }
  ]

  backend_secrets = [
    {
      name  = "azure-storage-key"
      value = module.storage.primary_access_key
    },
    {
      name  = "azure-search-key"
      value = module.ai_search.primary_admin_key
    },
    {
      name  = "azure-openai-key"
      value = module.openai.primary_access_key
    },
    {
      name  = "redis-password"
      value = module.redis.primary_access_key
    },
    {
      name  = "acr-password"
      value = module.container_registry.admin_password
    }
  ]

  acr_server   = module.container_registry.login_server
  acr_username = module.container_registry.admin_username

  tags = var.tags
}

# Static Web App for Frontend
module "static_web_app" {
  source = "./modules/static_web_app"

  name                = var.static_web_app_name
  resource_group_name = module.resource_group.name
  location            = var.static_web_app_location
  sku_tier            = var.static_web_app_sku

  app_settings = {
    VITE_API_BASE_URL = module.container_apps_env.backend_fqdn
  }

  tags = var.tags
}
