resource "azurerm_cognitive_account" "this" {
  name                = var.name
  resource_group_name = var.resource_group_name
  location            = var.location
  kind                = "OpenAI"
  sku_name            = var.sku_name

  custom_subdomain_name = var.name
  public_network_access_enabled = true

  tags = var.tags
}

# Chat Model Deployment (GPT-4o-mini)
resource "azurerm_cognitive_deployment" "chat" {
  name                 = var.deployments.chat.name
  cognitive_account_id = azurerm_cognitive_account.this.id

  model {
    format  = "OpenAI"
    name    = var.deployments.chat.model
    version = var.deployments.chat.version
  }

  scale {
    type     = "Standard"
    capacity = var.deployments.chat.capacity
  }
}

# Embedding Model Deployment
resource "azurerm_cognitive_deployment" "embedding" {
  name                 = var.deployments.embedding.name
  cognitive_account_id = azurerm_cognitive_account.this.id

  model {
    format  = "OpenAI"
    name    = var.deployments.embedding.model
    version = var.deployments.embedding.version
  }

  scale {
    type     = "Standard"
    capacity = var.deployments.embedding.capacity
  }

  depends_on = [azurerm_cognitive_deployment.chat]
}
