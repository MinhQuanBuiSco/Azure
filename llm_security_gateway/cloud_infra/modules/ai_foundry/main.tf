# Azure AI Services (formerly Cognitive Services) for Content Safety
resource "azurerm_cognitive_account" "content_safety" {
  name                = "ai-safety-${var.environment}-${var.name_suffix}"
  location            = var.location
  resource_group_name = var.resource_group_name
  kind                = "ContentSafety"
  sku_name            = "S0"
  tags                = var.tags

  custom_subdomain_name = "ai-safety-${var.environment}-${var.name_suffix}"
}

# Azure OpenAI Service
resource "azurerm_cognitive_account" "openai" {
  name                = "aoai-llm-gateway-${var.environment}-${var.name_suffix}"
  location            = var.location
  resource_group_name = var.resource_group_name
  kind                = "OpenAI"
  sku_name            = "S0"
  tags                = var.tags

  custom_subdomain_name = "aoai-llm-gateway-${var.environment}-${var.name_suffix}"
}

# GPT-4o Deployment
resource "azurerm_cognitive_deployment" "gpt4o" {
  name                 = "gpt-4o"
  cognitive_account_id = azurerm_cognitive_account.openai.id

  model {
    format  = "OpenAI"
    name    = "gpt-4o"
    version = "2024-05-13"
  }

  scale {
    type     = "Standard"
    capacity = 10
  }
}

# GPT-4o-mini Deployment
resource "azurerm_cognitive_deployment" "gpt4o_mini" {
  name                 = "gpt-4o-mini"
  cognitive_account_id = azurerm_cognitive_account.openai.id

  model {
    format  = "OpenAI"
    name    = "gpt-4o-mini"
    version = "2024-07-18"
  }

  scale {
    type     = "Standard"
    capacity = 20
  }

  depends_on = [azurerm_cognitive_deployment.gpt4o]
}

# Diagnostic settings for OpenAI
resource "azurerm_monitor_diagnostic_setting" "openai" {
  count = var.enable_diagnostics ? 1 : 0

  name                       = "openai-diagnostics"
  target_resource_id         = azurerm_cognitive_account.openai.id
  log_analytics_workspace_id = var.log_analytics_workspace_id

  enabled_log {
    category = "Audit"
  }

  enabled_log {
    category = "RequestResponse"
  }

  metric {
    category = "AllMetrics"
  }
}
