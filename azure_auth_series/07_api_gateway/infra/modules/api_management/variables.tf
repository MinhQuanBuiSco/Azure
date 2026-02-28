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
