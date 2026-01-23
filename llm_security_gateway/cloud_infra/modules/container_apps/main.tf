# Container Apps Environment
resource "azurerm_container_app_environment" "main" {
  name                       = "cae-llm-gateway-${var.environment}-${var.name_suffix}"
  location                   = var.location
  resource_group_name        = var.resource_group_name
  log_analytics_workspace_id = var.log_analytics_workspace_id
  tags                       = var.tags
}

# Backend Container App
resource "azurerm_container_app" "backend" {
  name                         = "ca-backend-${var.environment}-${var.name_suffix}"
  container_app_environment_id = azurerm_container_app_environment.main.id
  resource_group_name          = var.resource_group_name
  revision_mode                = "Single"
  tags                         = var.tags

  dynamic "registry" {
    for_each = var.registry_server != "" ? [1] : []
    content {
      server               = var.registry_server
      username             = var.registry_username
      password_secret_name = "registry-password"
    }
  }

  template {
    min_replicas = 1
    max_replicas = 10

    container {
      name   = "backend"
      image  = var.backend_image
      cpu    = 1
      memory = "2Gi"

      env {
        name  = "ENVIRONMENT"
        value = var.environment
      }

      env {
        name  = "AZURE_AI_ENDPOINT"
        value = var.azure_ai_endpoint
      }

      env {
        name        = "AZURE_AI_API_KEY"
        secret_name = "azure-ai-api-key"
      }

      env {
        name  = "AZURE_AI_DEPLOYMENT_NAME"
        value = var.azure_ai_deployment_name
      }

      env {
        name  = "AZURE_CONTENT_SAFETY_ENDPOINT"
        value = var.azure_content_safety_endpoint
      }

      env {
        name        = "AZURE_CONTENT_SAFETY_KEY"
        secret_name = "azure-content-safety-key"
      }

      env {
        name        = "REDIS_URL"
        secret_name = "redis-connection-string"
      }

      env {
        name        = "COSMOS_CONNECTION_STRING"
        secret_name = "cosmos-connection-string"
      }

      env {
        name  = "APPLICATIONINSIGHTS_CONNECTION_STRING"
        value = var.application_insights_connection_string
      }

      liveness_probe {
        path             = "/health"
        port             = 8000
        transport        = "HTTP"
        interval_seconds = 30
      }

      readiness_probe {
        path             = "/ready"
        port             = 8000
        transport        = "HTTP"
        interval_seconds = 10
      }
    }
  }

  ingress {
    external_enabled = true
    target_port      = 8000
    transport        = "auto"

    traffic_weight {
      percentage      = 100
      latest_revision = true
    }
  }

  secret {
    name  = "azure-ai-api-key"
    value = var.azure_ai_api_key
  }

  secret {
    name  = "azure-content-safety-key"
    value = var.azure_content_safety_key
  }

  secret {
    name  = "redis-connection-string"
    value = var.redis_connection_string
  }

  secret {
    name  = "cosmos-connection-string"
    value = var.cosmos_connection_string
  }

  dynamic "secret" {
    for_each = var.registry_password != "" ? [1] : []
    content {
      name  = "registry-password"
      value = var.registry_password
    }
  }
}

# Frontend Container App
resource "azurerm_container_app" "frontend" {
  name                         = "ca-frontend-${var.environment}-${var.name_suffix}"
  container_app_environment_id = azurerm_container_app_environment.main.id
  resource_group_name          = var.resource_group_name
  revision_mode                = "Single"
  tags                         = var.tags

  dynamic "registry" {
    for_each = var.registry_server != "" ? [1] : []
    content {
      server               = var.registry_server
      username             = var.registry_username
      password_secret_name = "registry-password"
    }
  }

  dynamic "secret" {
    for_each = var.registry_password != "" ? [1] : []
    content {
      name  = "registry-password"
      value = var.registry_password
    }
  }

  template {
    min_replicas = 1
    max_replicas = 5

    container {
      name   = "frontend"
      image  = var.frontend_image
      cpu    = 0.5
      memory = "1Gi"

      env {
        name  = "NEXT_PUBLIC_API_URL"
        value = "https://${azurerm_container_app.backend.ingress[0].fqdn}"
      }

      env {
        name  = "NODE_ENV"
        value = "production"
      }
    }
  }

  ingress {
    external_enabled = true
    target_port      = 3000
    transport        = "auto"

    traffic_weight {
      percentage      = 100
      latest_revision = true
    }
  }

  depends_on = [azurerm_container_app.backend]
}
