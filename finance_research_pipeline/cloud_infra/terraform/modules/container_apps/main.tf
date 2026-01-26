# Container Apps Environment
resource "azurerm_container_app_environment" "main" {
  name                       = "${var.project_name}-env-${var.environment}"
  location                   = var.location
  resource_group_name        = var.resource_group_name
  log_analytics_workspace_id = var.log_analytics_workspace_id

  tags = var.tags
}

# Backend Container App
resource "azurerm_container_app" "backend" {
  name                         = "${var.project_name}-backend-${var.environment}"
  container_app_environment_id = azurerm_container_app_environment.main.id
  resource_group_name          = var.resource_group_name
  revision_mode                = "Single"

  template {
    container {
      name   = "backend"
      image  = "${var.acr_login_server}/${var.backend_image_name}:${var.backend_image_tag}"
      cpu    = var.backend_cpu
      memory = var.backend_memory

      env {
        name  = "ENVIRONMENT"
        value = var.environment
      }

      env {
        name  = "DEBUG"
        value = var.environment == "dev" ? "true" : "false"
      }

      env {
        name  = "LOG_LEVEL"
        value = var.environment == "dev" ? "DEBUG" : "INFO"
      }

      env {
        name  = "LOG_FORMAT"
        value = "json"
      }

      env {
        name  = "LLM_PROVIDER"
        value = "azure_openai"
      }

      env {
        name        = "AZURE_OPENAI_ENDPOINT"
        secret_name = "azure-openai-endpoint"
      }

      env {
        name        = "AZURE_OPENAI_API_KEY"
        secret_name = "azure-openai-key"
      }

      env {
        name  = "AZURE_OPENAI_DEPLOYMENT_NAME"
        value = var.azure_openai_deployment_name
      }

      env {
        name        = "TAVILY_API_KEY"
        secret_name = "tavily-api-key"
      }

      env {
        name        = "NEWSAPI_KEY"
        secret_name = "newsapi-key"
      }

      env {
        name  = "REDIS_HOST"
        value = var.redis_host
      }

      env {
        name  = "REDIS_PORT"
        value = "6380"
      }

      env {
        name        = "REDIS_PASSWORD"
        secret_name = "redis-password"
      }

      env {
        name  = "REDIS_SSL"
        value = "true"
      }

      env {
        name  = "COSMOS_ENDPOINT"
        value = var.cosmos_endpoint
      }

      env {
        name        = "COSMOS_KEY"
        secret_name = "cosmos-key"
      }

      env {
        name  = "COSMOS_DATABASE"
        value = "finance_research"
      }

      env {
        name  = "CORS_ORIGINS"
        value = jsonencode(var.cors_origins)
      }

      liveness_probe {
        path             = "/health"
        port             = 8000
        transport        = "HTTP"
        initial_delay    = 30
        interval_seconds = 30
      }

      readiness_probe {
        path             = "/health"
        port             = 8000
        transport        = "HTTP"
        initial_delay    = 10
        interval_seconds = 10
      }
    }

    min_replicas = var.backend_min_replicas
    max_replicas = var.backend_max_replicas
  }

  secret {
    name  = "azure-openai-endpoint"
    value = var.azure_openai_endpoint
  }

  secret {
    name  = "azure-openai-key"
    value = var.azure_openai_api_key
  }

  secret {
    name  = "tavily-api-key"
    value = var.tavily_api_key
  }

  secret {
    name  = "newsapi-key"
    value = var.newsapi_key
  }

  secret {
    name  = "redis-password"
    value = var.redis_password
  }

  secret {
    name  = "cosmos-key"
    value = var.cosmos_key
  }

  registry {
    server               = var.acr_login_server
    username             = var.acr_admin_username
    password_secret_name = "acr-password"
  }

  secret {
    name  = "acr-password"
    value = var.acr_admin_password
  }

  ingress {
    external_enabled = true
    target_port      = 8000
    transport        = "http"

    traffic_weight {
      percentage      = 100
      latest_revision = true
    }
  }

  tags = var.tags
}

# Frontend Container App
resource "azurerm_container_app" "frontend" {
  name                         = "${var.project_name}-frontend-${var.environment}"
  container_app_environment_id = azurerm_container_app_environment.main.id
  resource_group_name          = var.resource_group_name
  revision_mode                = "Single"

  template {
    container {
      name   = "frontend"
      image  = "${var.acr_login_server}/${var.frontend_image_name}:${var.frontend_image_tag}"
      cpu    = var.frontend_cpu
      memory = var.frontend_memory

      liveness_probe {
        path             = "/health"
        port             = 80
        transport        = "HTTP"
        initial_delay    = 10
        interval_seconds = 30
      }
    }

    min_replicas = var.frontend_min_replicas
    max_replicas = var.frontend_max_replicas
  }

  registry {
    server               = var.acr_login_server
    username             = var.acr_admin_username
    password_secret_name = "acr-password"
  }

  secret {
    name  = "acr-password"
    value = var.acr_admin_password
  }

  ingress {
    external_enabled = true
    target_port      = 80
    transport        = "http"

    traffic_weight {
      percentage      = 100
      latest_revision = true
    }
  }

  tags = var.tags
}
