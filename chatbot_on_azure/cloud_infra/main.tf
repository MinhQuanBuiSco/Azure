terraform {
  required_version = ">= 1.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {
    resource_group {
      prevent_deletion_if_contains_resources = false
    }
  }
}

# Resource Group
resource "azurerm_resource_group" "main" {
  name     = var.resource_group_name
  location = var.location

  tags = var.tags
}

# Virtual Network
module "network" {
  source = "./modules/network"

  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  vnet_name           = "${var.project_name}-vnet"
  address_space       = var.vnet_address_space
  aks_subnet_prefix   = var.aks_subnet_prefix
  tags                = var.tags
}

# Azure Container Registry
module "acr" {
  source = "./modules/acr"

  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  acr_name            = var.acr_name
  sku                 = var.acr_sku
  tags                = var.tags
}

# Azure Kubernetes Service
module "aks" {
  source = "./modules/aks"

  resource_group_name   = azurerm_resource_group.main.name
  location              = azurerm_resource_group.main.location
  cluster_name          = var.aks_cluster_name
  dns_prefix            = var.aks_dns_prefix
  kubernetes_version    = var.kubernetes_version
  node_count            = var.aks_node_count
  vm_size               = var.aks_vm_size
  vnet_subnet_id        = module.network.aks_subnet_id
  tags                  = var.tags

  depends_on = [module.network]
}

# Grant AKS access to pull images from ACR
# COMMENTED OUT - Will be done manually due to permission issues
# Run this after terraform apply completes:
# az role assignment create --assignee <AKS_KUBELET_IDENTITY> --role AcrPull --scope <ACR_ID>
# resource "azurerm_role_assignment" "aks_acr_pull" {
#   principal_id                     = module.aks.kubelet_identity_object_id
#   role_definition_name             = "AcrPull"
#   scope                            = module.acr.acr_id
#   skip_service_principal_aad_check = true
# }

# Azure OpenAI Service - COMMENTED OUT DUE TO QUOTA LIMITS
# Use regular OpenAI API instead (see backend/.env.example)
# module "openai" {
#   source = "./modules/openai"
#
#   resource_group_name = azurerm_resource_group.main.name
#   location            = var.openai_location
#   account_name        = var.openai_account_name
#   sku_name            = var.openai_sku
#   deployment_name     = var.openai_deployment_name
#   model_name          = var.openai_model_name
#   model_version       = var.openai_model_version
#   deployment_capacity = var.openai_deployment_capacity
#   tags                = var.tags
# }
