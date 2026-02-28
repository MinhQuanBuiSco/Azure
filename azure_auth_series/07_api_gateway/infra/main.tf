terraform {
  required_version = ">= 1.5.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.100"
    }
  }
}

provider "azurerm" {
  features {}
}

# ── Resource Group ──────────────────────────────────────

module "resource_group" {
  source = "./modules/resource_group"

  name     = var.resource_group_name
  location = var.location

  tags = local.tags
}

# ── Container Registry ──────────────────────────────────

module "container_registry" {
  source = "./modules/container_registry"

  name                = var.acr_name
  resource_group_name = module.resource_group.name
  location            = module.resource_group.location

  tags = local.tags
}

# ── Container Apps (3 services) ─────────────────────────

module "container_apps" {
  source = "./modules/container_apps"

  project_name        = var.project_name
  resource_group_name = module.resource_group.name
  location            = module.resource_group.location

  acr_login_server   = module.container_registry.login_server
  acr_admin_username = module.container_registry.admin_username
  acr_admin_password = module.container_registry.admin_password

  tenant_id              = var.tenant_id
  task_api_client_id     = var.task_api_client_id
  task_api_client_secret = var.task_api_client_secret
  notification_client_id = var.notification_client_id
  audit_client_id        = var.audit_client_id
  allowed_origins        = var.allowed_origins

  tags = local.tags
}

# ── API Management ──────────────────────────────────────

module "api_management" {
  source = "./modules/api_management"

  apim_name           = var.apim_name
  resource_group_name = module.resource_group.name
  location            = module.resource_group.location
  publisher_email     = var.publisher_email

  tenant_id = var.tenant_id

  task_api_fqdn     = module.container_apps.task_api_fqdn
  notification_fqdn = module.container_apps.notification_fqdn
  audit_fqdn        = module.container_apps.audit_fqdn

  task_api_audience      = "api://${var.task_api_client_id}"
  notification_audience  = "api://${var.notification_client_id}"
  audit_audience         = "api://${var.audit_client_id}"

  tags = local.tags
}

# ── Locals ──────────────────────────────────────────────

locals {
  tags = {
    project = "azure-auth-series"
    blog    = "07-api-gateway"
  }
}
