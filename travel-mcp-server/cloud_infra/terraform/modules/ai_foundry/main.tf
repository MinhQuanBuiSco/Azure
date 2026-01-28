# Azure AI Foundry (Cognitive Services for OpenAI)
resource "azurerm_cognitive_account" "this" {
  name                  = var.name
  location              = var.location
  resource_group_name   = var.resource_group_name
  kind                  = "OpenAI"
  sku_name              = var.sku_name
  custom_subdomain_name = var.custom_subdomain_name

  identity {
    type = "SystemAssigned"
  }

  tags = var.tags
}

# OpenAI Model Deployment
resource "azurerm_cognitive_deployment" "openai" {
  name                 = var.model_deployment_name
  cognitive_account_id = azurerm_cognitive_account.this.id

  model {
    format  = "OpenAI"
    name    = var.model_name
    version = var.model_version
  }

  sku {
    name     = var.deployment_sku_name
    capacity = var.deployment_capacity
  }
}
