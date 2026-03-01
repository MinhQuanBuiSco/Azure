variable "project_name" {
  description = "Project name prefix"
  type        = string
  default     = "blog08-prod"
}

variable "resource_group_name" {
  description = "Resource group name"
  type        = string
  default     = "rg-blog08-production"
}

variable "location" {
  description = "Azure region"
  type        = string
  default     = "australiaeast"
}

variable "acr_name" {
  description = "Container registry name (globally unique, alphanumeric only)"
  type        = string
}

variable "apim_name" {
  description = "API Management instance name (globally unique)"
  type        = string
}

variable "publisher_email" {
  description = "Publisher email for API Management"
  type        = string
}

# ── Azure AD ───────────────────────────────────────────

variable "tenant_id" {
  description = "Azure AD tenant ID"
  type        = string
}

variable "task_api_client_id" {
  description = "Task API app registration client ID"
  type        = string
}

variable "task_api_client_secret" {
  description = "Task API app registration client secret"
  type        = string
  sensitive   = true
}

variable "notification_client_id" {
  description = "Notification Service app registration client ID"
  type        = string
}

variable "audit_client_id" {
  description = "Audit Service app registration client ID"
  type        = string
}

variable "allowed_origins" {
  description = "Allowed CORS origins (comma-separated)"
  type        = string
  default     = "http://localhost:3000"
}

# ── Monitoring ─────────────────────────────────────────

variable "alert_email" {
  description = "Email address for Azure Monitor alert notifications"
  type        = string
}
