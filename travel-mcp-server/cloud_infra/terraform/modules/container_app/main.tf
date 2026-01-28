resource "azurerm_container_app" "this" {
  name                         = var.name
  container_app_environment_id = var.container_app_environment_id
  resource_group_name          = var.resource_group_name
  revision_mode                = var.revision_mode
  tags                         = var.tags

  template {
    min_replicas = var.min_replicas
    max_replicas = var.max_replicas

    container {
      name   = var.container_name
      image  = var.image
      cpu    = var.cpu
      memory = var.memory

      dynamic "env" {
        for_each = { for idx, e in var.env_vars : idx => e }
        content {
          name  = env.value.name
          value = env.value.value
        }
      }

      dynamic "env" {
        for_each = { for idx, e in var.secret_env_vars : idx => e }
        content {
          name        = env.value.name
          secret_name = env.value.secret_name
        }
      }
    }
  }

  dynamic "secret" {
    for_each = { for idx, s in nonsensitive(var.secrets) : s.name => s }
    content {
      name  = secret.value.name
      value = secret.value.value
    }
  }

  dynamic "ingress" {
    for_each = var.ingress_enabled ? [1] : []
    content {
      external_enabled = var.ingress_external
      target_port      = var.ingress_target_port
      transport        = var.ingress_transport

      traffic_weight {
        percentage      = 100
        latest_revision = true
      }
    }
  }

  dynamic "registry" {
    for_each = var.registry_server != "" ? [1] : []
    content {
      server               = var.registry_server
      username             = var.registry_username
      password_secret_name = var.registry_password_secret_name
    }
  }
}
