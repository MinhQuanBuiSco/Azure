resource "azurerm_container_app_environment" "this" {
  name                       = var.environment_name
  resource_group_name        = var.resource_group_name
  location                   = var.location
  log_analytics_workspace_id = var.log_analytics_workspace_id

  tags = var.tags
}

# Backend Container App
resource "azurerm_container_app" "backend" {
  name                         = var.backend_app_name
  resource_group_name          = var.resource_group_name
  container_app_environment_id = azurerm_container_app_environment.this.id
  revision_mode                = "Single"

  registry {
    server               = var.acr_server
    username             = var.acr_username
    password_secret_name = "acr-password"
  }

  secret {
    name  = "acr-password"
    value = var.backend_secrets[4].value
  }

  secret {
    name  = "azure-storage-key"
    value = var.backend_secrets[0].value
  }

  secret {
    name  = "azure-search-key"
    value = var.backend_secrets[1].value
  }

  secret {
    name  = "azure-openai-key"
    value = var.backend_secrets[2].value
  }

  secret {
    name  = "redis-password"
    value = var.backend_secrets[3].value
  }

  template {
    min_replicas = var.backend_min_replicas
    max_replicas = var.backend_max_replicas

    container {
      name   = "backend"
      image  = var.backend_image
      cpu    = var.backend_cpu
      memory = var.backend_memory

      dynamic "env" {
        for_each = var.backend_env_vars
        content {
          name  = env.value.name
          value = env.value.value
        }
      }

      # Secret environment variables
      env {
        name        = "AZURE_STORAGE_CONNECTION_STRING"
        secret_name = "azure-storage-key"
      }

      env {
        name        = "AZURE_SEARCH_API_KEY"
        secret_name = "azure-search-key"
      }

      env {
        name        = "AZURE_OPENAI_API_KEY"
        secret_name = "azure-openai-key"
      }

      env {
        name        = "REDIS_PASSWORD"
        secret_name = "redis-password"
      }
    }

    http_scale_rule {
      name                = "http-scaling"
      concurrent_requests = 50
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
