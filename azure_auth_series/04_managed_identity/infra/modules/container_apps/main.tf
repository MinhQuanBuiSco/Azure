resource "azurerm_log_analytics_workspace" "this" {
  name                = "law-${var.environment_name}"
  resource_group_name = var.resource_group_name
  location            = var.location
  sku                 = "PerGB2018"
  retention_in_days   = 30

  tags = var.tags
}

resource "azurerm_container_app_environment" "this" {
  name                       = var.environment_name
  resource_group_name        = var.resource_group_name
  location                   = var.location
  log_analytics_workspace_id = azurerm_log_analytics_workspace.this.id

  tags = var.tags
}

resource "azurerm_container_app" "backend" {
  name                         = var.backend_app_name
  resource_group_name          = var.resource_group_name
  container_app_environment_id = azurerm_container_app_environment.this.id
  revision_mode                = "Single"

  # System-assigned managed identity — the teaching point of Blog 4
  identity {
    type = "SystemAssigned"
  }

  registry {
    server               = var.acr_server
    username             = var.acr_username
    password_secret_name = "acr-password"
  }

  secret {
    name  = "acr-password"
    value = var.acr_password
  }

  template {
    min_replicas = var.backend_min_replicas
    max_replicas = var.backend_max_replicas

    container {
      name   = "backend"
      # Use a placeholder image for initial provisioning.
      # deploy.sh will update this with the real backend image from ACR.
      image  = "mcr.microsoft.com/azuredocs/containerapps-helloworld:latest"
      cpu    = var.backend_cpu
      memory = var.backend_memory

      # Key Vault URL — triggers config.py to use Managed Identity
      env {
        name  = "AZURE_KEY_VAULT_URL"
        value = var.key_vault_url
      }

      # CORS: allow the Static Web App frontend
      env {
        name  = "ALLOWED_ORIGINS"
        value = var.allowed_origins
      }
    }
  }

  ingress {
    external_enabled = true
    target_port      = 8000
    transport        = "http"

    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
  }

  tags = var.tags
}
