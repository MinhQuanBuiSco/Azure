# ── Container App Environment ──────────────────────────

resource "azurerm_container_app_environment" "this" {
  name                       = "${var.project_name}-env"
  location                   = var.location
  resource_group_name        = var.resource_group_name
  log_analytics_workspace_id = var.log_analytics_workspace_id

  tags = var.tags
}

# ── Task API — external ingress (APIM routes here) ─────

resource "azurerm_container_app" "task_api" {
  name                         = "task-api"
  container_app_environment_id = azurerm_container_app_environment.this.id
  resource_group_name          = var.resource_group_name
  revision_mode                = "Single"

  tags = var.tags

  template {
    min_replicas = 1
    max_replicas = 3

    container {
      name   = "task-api"
      image  = "mcr.microsoft.com/k8se/quickstart:latest"
      cpu    = 0.25
      memory = "0.5Gi"

      env {
        name  = "AZURE_HOME_TENANT_ID"
        value = var.tenant_id
      }
      env {
        name  = "AZURE_API_CLIENT_ID"
        value = var.task_api_client_id
      }
      env {
        name        = "AZURE_API_CLIENT_SECRET"
        secret_name = "api-client-secret"
      }
      env {
        name  = "ALLOWED_TENANT_IDS"
        value = var.tenant_id
      }
      env {
        name  = "AZURE_NOTIFICATION_CLIENT_ID"
        value = var.notification_client_id
      }
      env {
        name  = "NOTIFICATION_URL"
        value = "https://${azurerm_container_app.notification.ingress[0].fqdn}"
      }
      env {
        name  = "AZURE_AUDIT_CLIENT_ID"
        value = var.audit_client_id
      }
      env {
        name  = "AUDIT_URL"
        value = "https://${azurerm_container_app.audit.ingress[0].fqdn}"
      }
      env {
        name  = "TRUST_GATEWAY"
        value = "true"
      }
      env {
        name  = "ALLOWED_ORIGINS"
        value = "${var.allowed_origins},https://${azurerm_container_app.frontend.ingress[0].fqdn}"
      }
      env {
        name        = "APPLICATIONINSIGHTS_CONNECTION_STRING"
        secret_name = "appinsights-connection-string"
      }

      liveness_probe {
        transport               = "HTTP"
        path                    = "/health"
        port                    = 8000
        initial_delay           = 10
        interval_seconds        = 30
        failure_count_threshold = 3
      }

      readiness_probe {
        transport               = "HTTP"
        path                    = "/health"
        port                    = 8000
        interval_seconds        = 10
        failure_count_threshold = 3
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

  secret {
    name  = "api-client-secret"
    value = var.task_api_client_secret
  }

  secret {
    name  = "appinsights-connection-string"
    value = var.appinsights_connection_string
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
}

# ── Notification Service — INTERNAL ingress ───────────

resource "azurerm_container_app" "notification" {
  name                         = "notification-svc"
  container_app_environment_id = azurerm_container_app_environment.this.id
  resource_group_name          = var.resource_group_name
  revision_mode                = "Single"

  tags = var.tags

  template {
    min_replicas = 1
    max_replicas = 3

    container {
      name   = "notification-svc"
      image  = "mcr.microsoft.com/k8se/quickstart:latest"
      cpu    = 0.25
      memory = "0.5Gi"

      env {
        name  = "AZURE_HOME_TENANT_ID"
        value = var.tenant_id
      }
      env {
        name  = "AZURE_NOTIFICATION_CLIENT_ID"
        value = var.notification_client_id
      }
      env {
        name  = "ALLOWED_TENANT_IDS"
        value = var.tenant_id
      }
      env {
        name  = "TRUST_GATEWAY"
        value = "true"
      }
      env {
        name        = "APPLICATIONINSIGHTS_CONNECTION_STRING"
        secret_name = "appinsights-connection-string"
      }

      liveness_probe {
        transport               = "HTTP"
        path                    = "/health"
        port                    = 8001
        initial_delay           = 10
        interval_seconds        = 30
        failure_count_threshold = 3
      }

      readiness_probe {
        transport               = "HTTP"
        path                    = "/health"
        port                    = 8001
        interval_seconds        = 10
        failure_count_threshold = 3
      }
    }
  }

  ingress {
    external_enabled = false
    target_port      = 8001
    transport        = "http"

    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
  }

  secret {
    name  = "appinsights-connection-string"
    value = var.appinsights_connection_string
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
}

# ── Audit Service — INTERNAL ingress ──────────────────

resource "azurerm_container_app" "audit" {
  name                         = "audit-svc"
  container_app_environment_id = azurerm_container_app_environment.this.id
  resource_group_name          = var.resource_group_name
  revision_mode                = "Single"

  tags = var.tags

  template {
    min_replicas = 1
    max_replicas = 3

    container {
      name   = "audit-svc"
      image  = "mcr.microsoft.com/k8se/quickstart:latest"
      cpu    = 0.25
      memory = "0.5Gi"

      env {
        name  = "AZURE_HOME_TENANT_ID"
        value = var.tenant_id
      }
      env {
        name  = "AZURE_AUDIT_CLIENT_ID"
        value = var.audit_client_id
      }
      env {
        name  = "ALLOWED_TENANT_IDS"
        value = var.tenant_id
      }
      env {
        name  = "TRUST_GATEWAY"
        value = "true"
      }
      env {
        name        = "APPLICATIONINSIGHTS_CONNECTION_STRING"
        secret_name = "appinsights-connection-string"
      }

      liveness_probe {
        transport               = "HTTP"
        path                    = "/health"
        port                    = 8002
        initial_delay           = 10
        interval_seconds        = 30
        failure_count_threshold = 3
      }

      readiness_probe {
        transport               = "HTTP"
        path                    = "/health"
        port                    = 8002
        interval_seconds        = 10
        failure_count_threshold = 3
      }
    }
  }

  ingress {
    external_enabled = false
    target_port      = 8002
    transport        = "http"

    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
  }

  secret {
    name  = "appinsights-connection-string"
    value = var.appinsights_connection_string
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
}

# ── Frontend — external ingress (Next.js) ─────────────

resource "azurerm_container_app" "frontend" {
  name                         = "frontend"
  container_app_environment_id = azurerm_container_app_environment.this.id
  resource_group_name          = var.resource_group_name
  revision_mode                = "Single"

  tags = var.tags

  template {
    min_replicas = 1
    max_replicas = 3

    container {
      name   = "frontend"
      image  = "mcr.microsoft.com/k8se/quickstart:latest"
      cpu    = 0.25
      memory = "0.5Gi"

      liveness_probe {
        transport               = "HTTP"
        path                    = "/"
        port                    = 3000
        initial_delay           = 10
        interval_seconds        = 30
        failure_count_threshold = 3
      }

      readiness_probe {
        transport               = "HTTP"
        path                    = "/"
        port                    = 3000
        interval_seconds        = 10
        failure_count_threshold = 3
      }
    }
  }

  ingress {
    external_enabled = true
    target_port      = 3000
    transport        = "http"

    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
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
}
