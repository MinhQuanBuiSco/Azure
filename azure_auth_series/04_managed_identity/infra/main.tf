terraform {
  required_version = ">= 1.5.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.116.0"
    }
  }
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

data "azurerm_client_config" "current" {}

# ── Resource Group ──────────────────────────────────

module "resource_group" {
  source = "./modules/resource_group"

  name     = var.resource_group_name
  location = var.location
  tags     = var.tags
}

# ── Container Registry (Basic) ─────────────────────

module "container_registry" {
  source = "./modules/container_registry"

  name                = var.acr_name
  resource_group_name = module.resource_group.name
  location            = var.location
  tags                = var.tags
}

# ── Key Vault (deployer access policy only) ────────

module "key_vault" {
  source = "./modules/key_vault"

  name                = var.key_vault_name
  resource_group_name = module.resource_group.name
  location            = var.location
  tenant_id           = data.azurerm_client_config.current.tenant_id
  deployer_object_id  = data.azurerm_client_config.current.object_id

  tags = var.tags
}

# ── Static Web App (Frontend — Free tier) ──────────

module "static_web_app" {
  source = "./modules/static_web_app"

  name                = var.static_web_app_name
  resource_group_name = module.resource_group.name
  location            = var.static_web_app_location
  tags                = var.tags
}

# ── Container Apps (Backend + Managed Identity) ────

module "container_apps" {
  source = "./modules/container_apps"

  environment_name    = var.container_apps_env_name
  resource_group_name = module.resource_group.name
  location            = var.location

  backend_app_name     = var.backend_app_name
  backend_image        = "${module.container_registry.login_server}/${var.backend_image_name}:${var.backend_image_tag}"
  backend_cpu          = var.backend_cpu
  backend_memory       = var.backend_memory
  backend_min_replicas = var.backend_min_replicas
  backend_max_replicas = var.backend_max_replicas

  key_vault_url   = module.key_vault.vault_uri
  allowed_origins = "https://${module.static_web_app.default_hostname},http://localhost:3000"

  acr_server   = module.container_registry.login_server
  acr_username = module.container_registry.admin_username
  acr_password = module.container_registry.admin_password

  tags = var.tags
}

# ── Key Vault access policy for Managed Identity ───
# Created after Container App so we have the MI principal ID

resource "azurerm_key_vault_access_policy" "container_app_mi" {
  key_vault_id = module.key_vault.id
  tenant_id    = data.azurerm_client_config.current.tenant_id
  object_id    = module.container_apps.managed_identity_principal_id

  secret_permissions = [
    "Get", "List",
  ]
}
