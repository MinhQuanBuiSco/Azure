# ── Log Analytics Workspace (shared with Container Apps) ─

resource "azurerm_log_analytics_workspace" "this" {
  name                = "${var.project_name}-logs"
  location            = var.location
  resource_group_name = var.resource_group_name
  sku                 = "PerGB2018"
  retention_in_days   = 30

  tags = var.tags
}

# ── Application Insights (backed by Log Analytics) ─────

resource "azurerm_application_insights" "this" {
  name                = "${var.project_name}-appinsights"
  location            = var.location
  resource_group_name = var.resource_group_name
  application_type    = "web"
  workspace_id        = azurerm_log_analytics_workspace.this.id

  tags = var.tags
}

# ── Action Group (email alerts) ────────────────────────

resource "azurerm_monitor_action_group" "email" {
  name                = "${var.project_name}-alerts"
  resource_group_name = var.resource_group_name
  short_name          = "blog08alert"

  email_receiver {
    name          = "admin"
    email_address = var.alert_email
  }

  tags = var.tags
}

# ── Alert: High error rate (>10 failed requests in 5m) ─

resource "azurerm_monitor_metric_alert" "high_error_rate" {
  name                = "${var.project_name}-high-error-rate"
  resource_group_name = var.resource_group_name
  scopes              = [azurerm_application_insights.this.id]
  severity            = 2
  frequency           = "PT1M"
  window_size         = "PT5M"
  description         = "Fires when more than 10 failed requests occur within 5 minutes"

  criteria {
    metric_namespace = "microsoft.insights/components"
    metric_name      = "requests/failed"
    aggregation      = "Count"
    operator         = "GreaterThan"
    threshold        = 10
  }

  action {
    action_group_id = azurerm_monitor_action_group.email.id
  }

  tags = var.tags
}

# ── Alert: Slow response time (avg > 5s over 5m) ──────

resource "azurerm_monitor_metric_alert" "slow_response" {
  name                = "${var.project_name}-slow-response"
  resource_group_name = var.resource_group_name
  scopes              = [azurerm_application_insights.this.id]
  severity            = 3
  frequency           = "PT1M"
  window_size         = "PT5M"
  description         = "Fires when average response time exceeds 5 seconds over 5 minutes"

  criteria {
    metric_namespace = "microsoft.insights/components"
    metric_name      = "requests/duration"
    aggregation      = "Average"
    operator         = "GreaterThan"
    threshold        = 5000
  }

  action {
    action_group_id = azurerm_monitor_action_group.email.id
  }

  tags = var.tags
}
