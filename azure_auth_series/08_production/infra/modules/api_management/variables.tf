variable "apim_name" {
  description = "API Management instance name (globally unique)"
  type        = string
}

variable "resource_group_name" {
  description = "Resource group name"
  type        = string
}

variable "location" {
  description = "Azure region"
  type        = string
}

variable "publisher_email" {
  description = "Publisher email for APIM"
  type        = string
}

variable "tags" {
  description = "Resource tags"
  type        = map(string)
  default     = {}
}

# ── Azure AD ───────────────────────────────────────────

variable "tenant_id" {
  description = "Azure AD tenant ID"
  type        = string
}

# ── Frontend FQDN ─────────────────────────────────────

variable "frontend_fqdn" {
  description = "Frontend Container App FQDN (for CORS)"
  type        = string
}

# ── Backend FQDNs ──────────────────────────────────────

variable "task_api_fqdn" {
  description = "Task API Container App FQDN"
  type        = string
}

variable "notification_fqdn" {
  description = "Notification Service Container App FQDN"
  type        = string
}

variable "audit_fqdn" {
  description = "Audit Service Container App FQDN"
  type        = string
}

# ── JWT Audiences ──────────────────────────────────────

variable "task_api_audience" {
  description = "Task API audience (api://{client_id})"
  type        = string
}

variable "notification_audience" {
  description = "Notification Service audience (api://{client_id})"
  type        = string
}

variable "audit_audience" {
  description = "Audit Service audience (api://{client_id})"
  type        = string
}

# ── Application Insights ─────────────────────────────

variable "appinsights_instrumentation_key" {
  description = "Application Insights instrumentation key for APIM logger"
  type        = string
  sensitive   = true
}

variable "appinsights_id" {
  description = "Application Insights resource ID"
  type        = string
}
