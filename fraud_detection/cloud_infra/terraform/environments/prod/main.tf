/**
 * Production Terraform configuration for fraud detection system
 * High availability with larger nodes, multiple AZs, and production-grade databases
 */

locals {
  environment = "prod"
  project     = "fraud-detection"
  location    = var.location

  common_tags = {
    Environment = local.environment
    Project     = local.project
    ManagedBy   = "terraform"
    CostCenter  = "production"
  }
}

# Resource Group
resource "azurerm_resource_group" "main" {
  name     = var.resource_group_name
  location = local.location
  tags     = local.common_tags
}

# ACR Module - Premium for geo-replication
module "acr" {
  source = "../../modules/acr"

  registry_name       = var.acr_name
  resource_group_name = azurerm_resource_group.main.name
  location            = local.location
  sku                 = "Standard" # Standard for production (Premium for geo-replication)
  admin_enabled       = false      # Use managed identity in production

  tags = local.common_tags
}

# AKS Module - Production configuration
module "aks" {
  source = "../../modules/aks"

  cluster_name        = var.aks_cluster_name
  resource_group_name = azurerm_resource_group.main.name
  location            = local.location
  kubernetes_version  = var.kubernetes_version

  # Production configuration
  vm_size             = "Standard_D2s_v3" # 2 vCPU, 8 GB RAM
  node_count          = 3
  enable_auto_scaling = true
  min_node_count      = 3
  max_node_count      = 8
  availability_zones  = ["1", "2", "3"]

  # ACR integration
  attach_acr = true
  acr_id     = module.acr.acr_id

  tags = local.common_tags

  depends_on = [azurerm_resource_group.main, module.acr]
}

# Databases Module - Production configuration
module "databases" {
  source = "../../modules/databases"

  resource_group_name = azurerm_resource_group.main.name
  location            = local.location

  # PostgreSQL configuration - Production
  postgres_name           = var.postgres_name
  postgres_version        = "15"
  postgres_admin_username = var.postgres_admin_username
  postgres_admin_password = var.postgres_admin_password
  postgres_sku            = "GP_Standard_D2s_v3" # General Purpose
  postgres_storage_mb     = 65536                # 64 GB
  database_name           = "fraud_detection"
  high_availability       = true
  backup_retention_days   = 30
  geo_redundant_backup    = true

  # Redis configuration - Standard with replication
  redis_name     = var.redis_name
  redis_sku      = "Standard"
  redis_family   = "C"
  redis_capacity = 1 # 1 GB

  # Network security
  enable_private_endpoints = var.enable_private_endpoints
  subnet_id                = var.private_endpoint_subnet_id

  tags = local.common_tags

  depends_on = [azurerm_resource_group.main]
}

# Azure Key Vault for secrets management
resource "azurerm_key_vault" "main" {
  name                       = "${var.project_prefix}-kv-${local.environment}"
  location                   = azurerm_resource_group.main.location
  resource_group_name        = azurerm_resource_group.main.name
  tenant_id                  = data.azurerm_client_config.current.tenant_id
  sku_name                   = "standard"
  soft_delete_retention_days = 90
  purge_protection_enabled   = true

  enable_rbac_authorization = true

  network_acls {
    default_action = "Deny"
    bypass         = "AzureServices"
    ip_rules       = var.allowed_ip_ranges
  }

  tags = local.common_tags
}

# Store database credentials in Key Vault
resource "azurerm_key_vault_secret" "postgres_password" {
  name         = "postgres-admin-password"
  value        = var.postgres_admin_password
  key_vault_id = azurerm_key_vault.main.id

  depends_on = [azurerm_role_assignment.kv_admin]
}

resource "azurerm_key_vault_secret" "redis_key" {
  name         = "redis-primary-key"
  value        = module.databases.redis_primary_key
  key_vault_id = azurerm_key_vault.main.id

  depends_on = [azurerm_role_assignment.kv_admin]
}

# Role assignment for Key Vault
resource "azurerm_role_assignment" "kv_admin" {
  scope                = azurerm_key_vault.main.id
  role_definition_name = "Key Vault Secrets Officer"
  principal_id         = data.azurerm_client_config.current.object_id
}

# Data source for current Azure config
data "azurerm_client_config" "current" {}

# Log Analytics Workspace for monitoring
resource "azurerm_log_analytics_workspace" "main" {
  name                = "${var.project_prefix}-logs-${local.environment}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  sku                 = "PerGB2018"
  retention_in_days   = 30

  tags = local.common_tags
}

# Application Insights
resource "azurerm_application_insights" "main" {
  name                = "${var.project_prefix}-appinsights-${local.environment}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  workspace_id        = azurerm_log_analytics_workspace.main.id
  application_type    = "web"

  tags = local.common_tags
}
