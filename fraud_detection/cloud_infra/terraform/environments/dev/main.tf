/**
 * Main Terraform configuration for fraud detection system (dev environment)
 * Cost-optimized with B2s nodes, Basic ACR, and minimal database resources
 */

locals {
  environment = "dev"
  project     = "fraud-detection"
  location    = var.location

  common_tags = {
    Environment = local.environment
    Project     = local.project
    ManagedBy   = "terraform"
  }
}

# Resource Group - must be created first
resource "azurerm_resource_group" "main" {
  name     = var.resource_group_name
  location = local.location
  tags     = local.common_tags
}

# ACR Module
module "acr" {
  source = "../../modules/acr"

  registry_name       = var.acr_name
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = "Basic"
  admin_enabled       = true

  tags = local.common_tags

  depends_on = [azurerm_resource_group.main]
}

# AKS Module
module "aks" {
  source = "../../modules/aks"

  cluster_name        = var.aks_cluster_name
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  kubernetes_version  = var.kubernetes_version

  # Cost-optimized configuration (1 node for demo, increase for production)
  vm_size             = var.vm_size
  node_count          = 1
  enable_auto_scaling = true
  min_node_count      = 1
  max_node_count      = 3

  # ACR integration
  attach_acr = true
  acr_id     = module.acr.acr_id

  tags = local.common_tags

  depends_on = [azurerm_resource_group.main, module.acr]
}

# Databases Module
module "databases" {
  source = "../../modules/databases"

  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location

  # PostgreSQL configuration
  postgres_name           = var.postgres_name
  postgres_version        = "15"
  postgres_admin_username = var.postgres_admin_username
  postgres_admin_password = var.postgres_admin_password
  postgres_sku            = "B_Standard_B1ms" # Cost-optimized
  postgres_storage_mb     = 32768             # 32 GB
  database_name           = "fraud_detection"

  # Redis configuration
  redis_name     = var.redis_name
  redis_sku      = "Basic"
  redis_family   = "C"
  redis_capacity = 0 # 250 MB for Basic C0

  tags = local.common_tags
}
