# ── Log Analytics + Container App Environment ──────────

resource "azurerm_log_analytics_workspace" "this" {
  name                = "${var.project_name}-logs"
  location            = var.location
  resource_group_name = var.resource_group_name
  sku                 = "PerGB2018"
  retention_in_days   = 30

  tags = var.tags
}

resource "azurerm_container_app_environment" "this" {
  name                       = "${var.project_name}-env"
  location                   = var.location
  resource_group_name        = var.resource_group_name
  log_analytics_workspace_id = azurerm_log_analytics_workspace.this.id

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
    min_replicas = 0
    max_replicas = 1

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

  secret {
    name  = "api-client-secret"
    value = var.task_api_client_secret
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

# ── Notification Service — external ingress ─────────────

resource "azurerm_container_app" "notification" {
  name                         = "notification-svc"
  container_app_environment_id = azurerm_container_app_environment.this.id
  resource_group_name          = var.resource_group_name
  revision_mode                = "Single"

  tags = var.tags

  template {
    min_replicas = 0
    max_replicas = 1

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
    }
  }

  ingress {
    external_enabled = true
    target_port      = 8001
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

# ── Audit Service — external ingress ────────────────────

resource "azurerm_container_app" "audit" {
  name                         = "audit-svc"
  container_app_environment_id = azurerm_container_app_environment.this.id
  resource_group_name          = var.resource_group_name
  revision_mode                = "Single"

  tags = var.tags

  template {
    min_replicas = 0
    max_replicas = 1

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
    }
  }

  ingress {
    external_enabled = true
    target_port      = 8002
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
