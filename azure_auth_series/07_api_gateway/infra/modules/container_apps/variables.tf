variable "project_name" {
  description = "Project name prefix for resources"
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

variable "tags" {
  description = "Resource tags"
  type        = map(string)
  default     = {}
}

# ── ACR ────────────────────────────────────────────────

variable "acr_login_server" {
  description = "ACR login server URL"
  type        = string
}

variable "acr_admin_username" {
  description = "ACR admin username"
  type        = string
}

variable "acr_admin_password" {
  description = "ACR admin password"
  type        = string
  sensitive   = true
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
