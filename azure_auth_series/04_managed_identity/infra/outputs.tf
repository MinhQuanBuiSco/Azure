# ── URLs ────────────────────────────────────────────

output "backend_url" {
  description = "Backend API URL (Container Apps)"
  value       = module.container_apps.backend_url
}

output "frontend_url" {
  description = "Frontend URL (Static Web Apps)"
  value       = "https://${module.static_web_app.default_hostname}"
}

# ── Key Vault ──────────────────────────────────────

output "key_vault_name" {
  description = "Key Vault name (for deploy.sh to seed secrets)"
  value       = module.key_vault.name
}

output "key_vault_uri" {
  description = "Key Vault URI"
  value       = module.key_vault.vault_uri
}

# ── Container Registry ─────────────────────────────

output "acr_login_server" {
  description = "ACR login server (for docker push)"
  value       = module.container_registry.login_server
}

# ── Static Web App ─────────────────────────────────

output "swa_deployment_token" {
  description = "SWA deployment token (for swa-cli deploy)"
  value       = module.static_web_app.api_key
  sensitive   = true
}

# ── Resource Group ─────────────────────────────────

output "resource_group_name" {
  value = module.resource_group.name
}

# ── Container App ──────────────────────────────────

output "backend_app_name" {
  value = var.backend_app_name
}
