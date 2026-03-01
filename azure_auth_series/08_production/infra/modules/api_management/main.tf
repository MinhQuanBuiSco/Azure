# ── APIM Instance (Developer tier) ──────────────────────

resource "azurerm_api_management" "this" {
  name                = var.apim_name
  location            = var.location
  resource_group_name = var.resource_group_name
  publisher_name      = "Azure Auth Series"
  publisher_email     = var.publisher_email
  sku_name            = "Developer_1"

  identity {
    type = "SystemAssigned"
  }

  tags = var.tags
}

# ── Application Insights Logger + Diagnostic ──────────

resource "azurerm_api_management_logger" "appinsights" {
  name                = "appinsights-logger"
  api_management_name = azurerm_api_management.this.name
  resource_group_name = var.resource_group_name

  application_insights {
    instrumentation_key = var.appinsights_instrumentation_key
  }
}

resource "azurerm_api_management_diagnostic" "appinsights" {
  identifier               = "applicationinsights"
  api_management_name      = azurerm_api_management.this.name
  resource_group_name      = var.resource_group_name
  api_management_logger_id = azurerm_api_management_logger.appinsights.id

  sampling_percentage       = 100
  always_log_errors         = true
  log_client_ip             = true
  verbosity                 = "information"
  http_correlation_protocol = "W3C"

  frontend_request {
    body_bytes     = 0
    headers_to_log = ["X-User-OID", "X-Tenant-ID"]
  }

  frontend_response {
    body_bytes = 0
  }

  backend_request {
    body_bytes = 0
  }

  backend_response {
    body_bytes = 0
  }
}

# ════════════════════════════════════════════════════════
# Task API
# ════════════════════════════════════════════════════════

resource "azurerm_api_management_api" "task_api" {
  name                = "task-api"
  resource_group_name = var.resource_group_name
  api_management_name = azurerm_api_management.this.name
  revision            = "1"
  display_name        = "Task API"
  path                = "api"
  protocols           = ["https"]
  service_url         = "https://${var.task_api_fqdn}/api"

  subscription_required = false
}

# -- Task API Operations --
# url_template is RELATIVE to the API path ("api").
# Frontend calls: https://gateway/api/me → APIM strips "api" prefix → matches "/me"
# Backend receives: service_url + "/me" = https://backend/api/me ✓

resource "azurerm_api_management_api_operation" "get_me" {
  operation_id        = "get-me"
  api_name            = azurerm_api_management_api.task_api.name
  api_management_name = azurerm_api_management.this.name
  resource_group_name = var.resource_group_name
  display_name        = "Get Current User"
  method              = "GET"
  url_template        = "/me"
}

resource "azurerm_api_management_api_operation" "get_tasks" {
  operation_id        = "get-tasks"
  api_name            = azurerm_api_management_api.task_api.name
  api_management_name = azurerm_api_management.this.name
  resource_group_name = var.resource_group_name
  display_name        = "List Tasks"
  method              = "GET"
  url_template        = "/tasks"
}

resource "azurerm_api_management_api_operation" "create_task" {
  operation_id        = "create-task"
  api_name            = azurerm_api_management_api.task_api.name
  api_management_name = azurerm_api_management.this.name
  resource_group_name = var.resource_group_name
  display_name        = "Create Task"
  method              = "POST"
  url_template        = "/tasks"
}

resource "azurerm_api_management_api_operation" "update_task" {
  operation_id        = "update-task"
  api_name            = azurerm_api_management_api.task_api.name
  api_management_name = azurerm_api_management.this.name
  resource_group_name = var.resource_group_name
  display_name        = "Update Task"
  method              = "PATCH"
  url_template        = "/tasks/{taskId}"

  template_parameter {
    name     = "taskId"
    required = true
    type     = "integer"
  }
}

resource "azurerm_api_management_api_operation" "delete_task" {
  operation_id        = "delete-task"
  api_name            = azurerm_api_management_api.task_api.name
  api_management_name = azurerm_api_management.this.name
  resource_group_name = var.resource_group_name
  display_name        = "Delete Task"
  method              = "DELETE"
  url_template        = "/tasks/{taskId}"

  template_parameter {
    name     = "taskId"
    required = true
    type     = "integer"
  }
}

# -- Task API Policy --

resource "azurerm_api_management_api_policy" "task_api" {
  api_name            = azurerm_api_management_api.task_api.name
  api_management_name = azurerm_api_management.this.name
  resource_group_name = var.resource_group_name

  xml_content = templatefile("${path.module}/policies/task-api.xml", {
    tenant_id       = var.tenant_id
    audience        = var.task_api_audience
    frontend_origin = "https://${var.frontend_fqdn}"
  })
}

# ════════════════════════════════════════════════════════
# Notification API
# ════════════════════════════════════════════════════════

resource "azurerm_api_management_api" "notification" {
  name                = "notification-api"
  resource_group_name = var.resource_group_name
  api_management_name = azurerm_api_management.this.name
  revision            = "1"
  display_name        = "Notification API"
  path                = "notification"
  protocols           = ["https"]
  service_url         = "https://${var.notification_fqdn}"

  subscription_required = false
}

resource "azurerm_api_management_api_operation" "send_notification" {
  operation_id        = "send-notification"
  api_name            = azurerm_api_management_api.notification.name
  api_management_name = azurerm_api_management.this.name
  resource_group_name = var.resource_group_name
  display_name        = "Send Notification"
  method              = "POST"
  url_template        = "/notify"
}

resource "azurerm_api_management_api_operation" "list_notifications" {
  operation_id        = "list-notifications"
  api_name            = azurerm_api_management_api.notification.name
  api_management_name = azurerm_api_management.this.name
  resource_group_name = var.resource_group_name
  display_name        = "List Notifications"
  method              = "GET"
  url_template        = "/notifications"
}

resource "azurerm_api_management_api_policy" "notification" {
  api_name            = azurerm_api_management_api.notification.name
  api_management_name = azurerm_api_management.this.name
  resource_group_name = var.resource_group_name

  xml_content = templatefile("${path.module}/policies/notification.xml", {
    tenant_id       = var.tenant_id
    audience        = var.notification_audience
    frontend_origin = "https://${var.frontend_fqdn}"
  })
}

# ════════════════════════════════════════════════════════
# Audit API
# ════════════════════════════════════════════════════════

resource "azurerm_api_management_api" "audit" {
  name                = "audit-api"
  resource_group_name = var.resource_group_name
  api_management_name = azurerm_api_management.this.name
  revision            = "1"
  display_name        = "Audit API"
  path                = "auditing"
  protocols           = ["https"]
  service_url         = "https://${var.audit_fqdn}"

  subscription_required = false
}

resource "azurerm_api_management_api_operation" "create_audit" {
  operation_id        = "create-audit"
  api_name            = azurerm_api_management_api.audit.name
  api_management_name = azurerm_api_management.this.name
  resource_group_name = var.resource_group_name
  display_name        = "Create Audit Entry"
  method              = "POST"
  url_template        = "/audit"
}

resource "azurerm_api_management_api_operation" "list_audit" {
  operation_id        = "list-audit"
  api_name            = azurerm_api_management_api.audit.name
  api_management_name = azurerm_api_management.this.name
  resource_group_name = var.resource_group_name
  display_name        = "List Audit Entries"
  method              = "GET"
  url_template        = "/audit"
}

resource "azurerm_api_management_api_policy" "audit" {
  api_name            = azurerm_api_management_api.audit.name
  api_management_name = azurerm_api_management.this.name
  resource_group_name = var.resource_group_name

  xml_content = templatefile("${path.module}/policies/audit.xml", {
    tenant_id       = var.tenant_id
    audience        = var.audit_audience
    frontend_origin = "https://${var.frontend_fqdn}"
  })
}
